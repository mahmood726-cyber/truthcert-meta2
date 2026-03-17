"""Meta2 simulation suite runner: Phase 1 + governance overlay.

Extends Phase 1 with:
  - Question Contract (estimand lock)
  - Bias decomposition
  - 3-witness panel (Classic FE, delta-engine, Selection witness)
  - Conservative arbitration
  - Calibration + decision-regret scoring

Usage:
    python -m sim.run_suite --config configs/suite_12topics_meta2.json --out outputs/runs
"""

import argparse
import hashlib
import json
import math
import time
from pathlib import Path

from scipy.stats import norm

Z_ALPHA_05 = norm.ppf(0.975)

import numpy as np
import pandas as pd

from .arbitration import arbitrate
from .bias_decomposition import compute_bias_profiles
from .calibration import calibration_metrics, aggregate_calibration
from .config_schema import SimulationConfig, TopicConfig
from .decision import decide, decide_denom_only
from .fit_delta import fit_delta
from .generate_trials import generate_trials
from .generate_truth import generate_truth
from .meta_fixed import fixed_effect, random_effects_dl
from .observed_world import build_observed_world
from .oracle import apply_oracle_shift, oracle_meta_per_node
from .propagate_engine import propagate
from .question_contract import QuestionContract
from .regret import compute_regret, aggregate_regret
from .score import compute_scores
from .seed import make_rng
from .selection import apply_selection
from .selection_witness import selection_witness
from .witness_panel import build_witness_panel


def _build_contract(topic_cfg: TopicConfig) -> QuestionContract:
    """Derive a QuestionContract from the topic config."""
    return QuestionContract(
        population=f"Simulated {topic_cfg.label}",
        intervention_classes=topic_cfg.node_grid.classes,
        comparator="control",
        endpoints=topic_cfg.node_grid.endpoints,
        effect_measure="logRR",
        missingness_policy="denominator_delta",
        decision_utility="conservative",
        mapping_confidence_rules={},
    )


def run_topic(topic_cfg: TopicConfig, seed_master: int,
              n_reps: int) -> dict:
    """Run all replications for a topic with Meta2 governance.

    Returns dict with rep_results, calibrations, regrets, contract_hash.
    """
    contract = _build_contract(topic_cfg)
    c_hash = contract.contract_hash()

    arb_cfg = topic_cfg.engine.arbitration
    thresh_low = arb_cfg.thresh_low
    thresh_high = arb_cfg.thresh_high
    inflate_mid = arb_cfg.inflate_mid
    inflate_high = arb_cfg.inflate_high
    ep_miss_thresh = arb_cfg.endpoint_missing_threshold

    rep_results = []
    calibrations = []
    regrets = []
    all_cal_items = []  # raw per-node calibration items for sharpness

    for rep in range(n_reps):
        rng = make_rng(seed_master, topic_cfg.topic_id, rep)

        # ── Phase 1 pipeline ──────────────────────────────────────────
        node_params = generate_truth(topic_cfg, rng)
        trials_df = generate_trials(topic_cfg, node_params, rng)
        trials_df = apply_oracle_shift(trials_df, topic_cfg, rng)
        trials_df = apply_selection(trials_df, topic_cfg, rng)
        observed_effects, node_denoms = build_observed_world(
            trials_df, topic_cfg)

        # Classic meta (published only, random-effects for fair comparison)
        classic_metas = {}
        pub_obs = observed_effects[observed_effects["has_pub"]]
        for nid, grp in pub_obs.groupby("node_id"):
            classic_metas[nid] = random_effects_dl(
                grp["logRR"].values, grp["se"].values)

        # Observed meta (all observed effects, RE for consistency)
        observed_metas = {}
        for nid, grp in observed_effects.groupby("node_id"):
            observed_metas[nid] = random_effects_dl(
                grp["logRR"].values, grp["se"].values)

        # Delta fit + propagate
        delta_posteriors = fit_delta(observed_metas, node_denoms, topic_cfg)
        propagated = propagate(
            observed_metas, node_denoms, delta_posteriors, topic_cfg, rng,
            observed_effects_df=observed_effects)

        # Oracle meta
        oracle_metas = oracle_meta_per_node(trials_df)

        # Denominator dict
        denom_dict = {}
        for _, row in node_denoms.iterrows():
            denom_dict[row["node_id"]] = row.to_dict()

        # Phase 1 decisions
        p1_decisions = {}
        denom_only_decisions = {}
        for nid in set(list(propagated) + list(oracle_metas)):
            dd = denom_dict.get(nid, {})
            if nid in propagated:
                p1_decisions[nid] = decide(propagated[nid], dd, topic_cfg)
            else:
                p1_decisions[nid] = {"label": "Insufficient",
                                     "reason": "no propagated"}
            denom_only_decisions[nid] = decide_denom_only(dd)

        # ── Phase 2: Meta2 governance ─────────────────────────────────
        bias_profiles = compute_bias_profiles(node_denoms)

        # Selection witness per node
        sel_witnesses = {}
        for nid, grp in observed_effects.groupby("node_id"):
            lrr = grp["logRR"].values
            se = grp["se"].values
            z = np.where(se > 0, lrr / se, 0.0)
            sb = (z < -Z_ALPHA_05).astype(float)
            sh = (z > Z_ALPHA_05).astype(float)
            sel_witnesses[nid] = selection_witness(lrr, se, sb, sh)

        # Build panels, arbitrate, decide
        all_nodes = set(list(observed_metas) + list(oracle_metas)
                        + list(propagated))
        cal_items = []
        regret_items = []
        node_results_map = {}

        for nid in all_nodes:
            classic = classic_metas.get(nid, {})
            engine = propagated.get(nid, {})
            sel = sel_witnesses.get(nid, {})
            oracle = oracle_metas.get(nid, {})
            dd = denom_dict.get(nid, {})
            bp = bias_profiles.get(nid)

            panel = build_witness_panel(classic, engine, sel)
            arb = arbitrate(panel, thresh_low, thresh_high,
                            inflate_mid, inflate_high)

            arb_decision = _meta2_decide(
                propagated.get(nid, {}), dd, topic_cfg, arb, bp,
                endpoint_missing_threshold=ep_miss_thresh)

            # Classic decision: fair 4-tier using RE CI + p-value analog.
            # Mirrors the engine's Recommend/Consider/Research/DoNot tiers
            # so regret comparison is symmetric.
            classic_dec = _classic_decide_re(classic)

            node_results_map[nid] = {
                "observed_meta": observed_metas.get(nid, {}),
                "classic_meta": classic,
                "oracle_meta": oracle,
                "engine_propagated": engine,
                "engine_decision": p1_decisions.get(nid, {}),
                "denom_only_decision": denom_only_decisions.get(nid, {}),
                "node_denom": dd,
                "witnesses": {k: v.to_dict() for k, v in panel.items()},
                "arbitration": arb.to_dict(),
                "arb_decision": arb_decision,
                "bias_profile": bp.model_dump() if bp else {},
                "contract_hash": c_hash,
            }

            oracle_mu = oracle.get("mu", np.nan)
            cal_items.append({
                "oracle_mu": oracle_mu,
                "arb_ci_low": arb.ci_low,
                "arb_ci_high": arb.ci_high,
                "delta_ci_low": engine.get("mu_cri_low", np.nan),
                "delta_ci_high": engine.get("mu_cri_high", np.nan),
                "classic_ci_low": classic.get("ci_low", np.nan),
                "classic_ci_high": classic.get("ci_high", np.nan),
                "arb_width": arb.ci_high - arb.ci_low,
                "delta_width": (engine.get("mu_cri_high", np.nan)
                                - engine.get("mu_cri_low", np.nan)),
                "classic_width": (classic.get("ci_high", np.nan)
                                  - classic.get("ci_low", np.nan)),
            })
            regret_items.append({
                "oracle_mu": oracle_mu,
                "classic_decision": classic_dec,
                "delta_decision": p1_decisions.get(nid, {}).get(
                    "label", "Insufficient"),
                "arb_decision": arb_decision.get("label", "Insufficient"),
            })

        calibrations.append(calibration_metrics(cal_items))
        regrets.append(compute_regret(regret_items))
        all_cal_items.extend(cal_items)

        rep_results.append({
            "topic_id": topic_cfg.topic_id,
            "rep": rep,
            "node_results": node_results_map,
            "delta_posteriors": {
                ep: {"summary": dp["summary"]}
                for ep, dp in delta_posteriors.items()
            },
        })

    return {
        "rep_results": rep_results,
        "calibrations": calibrations,
        "regrets": regrets,
        "contract_hash": c_hash,
        "_cal_items": all_cal_items,
    }


def _meta2_decide(propagated_node, node_denom, cfg,
                   arb_result, bias_profile,
                   endpoint_missing_threshold: float = 0.40) -> dict:
    """Meta2 decision with arbitration gates.

    Gates apply symmetrically: under high disagreement, both benefit
    recommendations AND definitive blocks are moved to Research (epistemic
    humility — if witnesses disagree strongly, we cannot confidently
    recommend OR block).
    """
    base = decide(propagated_node, node_denom, cfg)
    label = base["label"]
    reason = base["reason"]

    # Gate 1: high disagreement -> cap at Research (symmetric)
    if arb_result.decision_downgrade:
        if label in ("Recommend", "Consider-benefit"):
            return {"label": "Research",
                    "reason": reason + " | arb:high_disagreement(benefit)"}
        if label in ("DoNot", "Consider-harm"):
            return {"label": "Research",
                    "reason": reason + " | arb:high_disagreement(block)"}

    # Gate 2: high endpoint-missing rate -> cap benefit at Research
    if bias_profile is not None:
        if bias_profile.endpoint_missing_rate > endpoint_missing_threshold:
            if label in ("Recommend", "Consider-benefit"):
                return {"label": "Research",
                        "reason": reason + " | gate:endpoint_missing"}

    return {"label": label, "reason": reason + " | arb:" + arb_result.level}


def _classic_decide_re(classic_meta: dict) -> str:
    """Fair 4-tier decision from RE meta-analysis CI.

    Mirrors the engine's tier structure:
      Recommend:       CI entirely below 0 (strong benefit evidence)
      Consider:        point estimate < 0, CI crosses 0, but narrow
      Research:        CI very wide or near null
      DoNot:           CI entirely above 0 (harm evidence)
      Insufficient:    missing data
    """
    mu = classic_meta.get("mu")
    ci_lo = classic_meta.get("ci_low")
    ci_hi = classic_meta.get("ci_high")

    if mu is None or not math.isfinite(mu):
        return "Insufficient"
    if ci_lo is None or ci_hi is None:
        return "Insufficient"
    if not (math.isfinite(ci_lo) and math.isfinite(ci_hi)):
        return "Insufficient"

    width = ci_hi - ci_lo

    # Entirely below null → strong benefit
    if ci_hi < 0:
        return "Recommend"
    # Entirely above null → harm
    if ci_lo > 0:
        return "DoNot"
    # Crosses null — classify by strength + width
    if mu < 0 and width < 0.6:
        return "Consider-benefit"
    if mu > 0 and width < 0.6:
        return "Consider-harm"
    return "Research"


def run_suite(config_path: str, out_dir: str) -> Path:
    """Run the full Meta2 simulation suite."""
    with open(config_path, "r") as f:
        raw = json.load(f)
    cfg = SimulationConfig(**raw)

    # Hash config content (not path) for cross-machine reproducibility
    config_bytes = json.dumps(raw, sort_keys=True).encode()
    run_id = hashlib.sha256(
        f"meta2:{cfg.seed_master}:".encode() + config_bytes).hexdigest()[:12]
    run_dir = Path(out_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"Run ID:       {run_id}")
    print(f"Output:       {run_dir}")
    print(f"Topics:       {len(cfg.topics)}")
    print(f"Replications: {cfg.n_replications}")
    print()

    all_topic_rows = []
    all_capsules = []

    for topic_cfg in cfg.topics:
        t0 = time.time()
        print(f"  [{topic_cfg.topic_id}] {topic_cfg.label} ...", end=" ",
              flush=True)

        result = run_topic(topic_cfg, cfg.seed_master,
                           cfg.n_replications)

        p1_scores = compute_scores(result["rep_results"], topic_cfg)
        tm = p1_scores["topic_metrics"]
        tm["topic_id"] = topic_cfg.topic_id
        tm["label"] = topic_cfg.label

        cal_agg = aggregate_calibration(result["calibrations"])
        tm["coverage_arb"] = cal_agg.get("coverage_arb", np.nan)
        tm["coverage_delta"] = cal_agg.get("coverage_delta", np.nan)
        tm["coverage_classic"] = cal_agg.get("coverage_classic", np.nan)

        # Sharpness: mean interval width (lower = sharper, conditional on coverage)
        raw_cal = result.get("_cal_items", [])
        if raw_cal:
            tm["width_arb"] = float(np.nanmean(
                [c["arb_width"] for c in raw_cal]))
            tm["width_delta"] = float(np.nanmean(
                [c["delta_width"] for c in raw_cal]))
            tm["width_classic"] = float(np.nanmean(
                [c["classic_width"] for c in raw_cal]))
        else:
            tm["width_arb"] = np.nan
            tm["width_delta"] = np.nan
            tm["width_classic"] = np.nan

        reg_agg = aggregate_regret(result["regrets"])
        tm["regret_classic"] = reg_agg.get("regret_classic", np.nan)
        tm["regret_delta"] = reg_agg.get("regret_delta", np.nan)
        tm["regret_arb"] = reg_agg.get("regret_arb", np.nan)
        tm["contract_hash"] = result["contract_hash"]

        all_topic_rows.append(tm)

        last_rep = result["rep_results"][-1]
        for nid, nr in last_rep["node_results"].items():
            all_capsules.append({
                "topic_id": topic_cfg.topic_id,
                "node_id": nid,
                "contract_hash": nr.get("contract_hash", ""),
                "bias_profile": nr.get("bias_profile", {}),
                "witnesses": nr.get("witnesses", {}),
                "arbitration": nr.get("arbitration", {}),
                "arb_decision": nr.get("arb_decision", {}),
            })

        elapsed = time.time() - t0
        cov = cal_agg.get("coverage_arb", 0)
        reg = reg_agg.get("regret_arb", 0)
        print(f"({elapsed:.1f}s) cov_arb={cov:.3f} reg_arb={reg:.3f}")

    # Write outputs
    pd.DataFrame(all_topic_rows).to_csv(
        run_dir / "topic_metrics.csv", index=False)

    with open(run_dir / "node_capsules.jsonl", "w") as f:
        for cap in all_capsules:
            f.write(json.dumps(cap, default=str) + "\n")

    cov_arb = np.nanmean([r.get("coverage_arb", np.nan)
                          for r in all_topic_rows])
    cov_d = np.nanmean([r.get("coverage_delta", np.nan)
                        for r in all_topic_rows])
    cov_cl = np.nanmean([r.get("coverage_classic", np.nan)
                         for r in all_topic_rows])
    r_arb = np.nanmean([r.get("regret_arb", np.nan)
                        for r in all_topic_rows])
    r_cl = np.nanmean([r.get("regret_classic", np.nan)
                       for r in all_topic_rows])
    r_d = np.nanmean([r.get("regret_delta", np.nan)
                      for r in all_topic_rows])
    w_arb = np.nanmean([r.get("width_arb", np.nan)
                        for r in all_topic_rows])
    w_d = np.nanmean([r.get("width_delta", np.nan)
                      for r in all_topic_rows])
    w_cl = np.nanmean([r.get("width_classic", np.nan)
                       for r in all_topic_rows])

    pd.DataFrame([{
        "coverage_arb": float(cov_arb),
        "coverage_delta": float(cov_d),
        "coverage_classic": float(cov_cl),
        "regret_arb": float(r_arb),
        "regret_classic": float(r_cl),
        "regret_delta": float(r_d),
        "width_arb": float(w_arb),
        "width_delta": float(w_d),
        "width_classic": float(w_cl),
        "n_topics": len(cfg.topics),
        "n_replications": cfg.n_replications,
    }]).to_csv(run_dir / "global_metrics.csv", index=False)

    with open(run_dir / "manifest.json", "w") as f:
        json.dump({
            "run_id": run_id,
            "config_path": str(config_path),
            "framework": "meta2",
            "seed_master": cfg.seed_master,
            "n_replications": cfg.n_replications,
            "n_topics": len(cfg.topics),
        }, f, indent=2)

    print()
    print("=" * 64)
    print(f"META2 GLOBAL  (topics={len(cfg.topics)}, "
          f"reps={cfg.n_replications})")
    print(f"  Coverage (arb):      {cov_arb:.4f}")
    print(f"  Coverage (delta):    {cov_d:.4f}")
    print(f"  Coverage (classic):  {cov_cl:.4f}")
    print(f"  Regret (arb):        {r_arb:.4f}")
    print(f"  Regret (classic):    {r_cl:.4f}")
    print(f"  Regret (delta):      {r_d:.4f}")
    print(f"  Width (arb):         {w_arb:.4f}")
    print(f"  Width (delta):       {w_d:.4f}")
    print(f"  Width (classic):     {w_cl:.4f}")
    print("=" * 64)
    return run_dir


def main():
    parser = argparse.ArgumentParser(
        description="TruthCert Meta2 Prototype Suite")
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", default="outputs/runs")
    args = parser.parse_args()
    run_suite(args.config, args.out)


if __name__ == "__main__":
    main()
