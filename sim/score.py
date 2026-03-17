"""Scoring metrics: delta identifiability, coverage, false reassurance,
engine false reassurance, and convergence check.

All metrics are computed per-replication then averaged across replications.
"""

import math
from typing import List

import numpy as np

from .config_schema import TopicConfig


def compute_scores(topic_results: list, cfg: TopicConfig) -> dict:
    """Compute Phase-1 primary outcome metrics.

    Args:
        topic_results: list of per-replication dicts containing:
            node_results  : dict[node_id] -> {oracle_meta, classic_meta,
                            engine_propagated, engine_decision,
                            denom_only_decision, node_denom}
            delta_posteriors : dict[endpoint] -> {summary}
        cfg: TopicConfig

    Returns {topic_metrics: dict, delta_metrics: dict[endpoint -> dict]}.
    """
    n_reps = len(topic_results)

    classic_fr_rates: List[float] = []
    engine_fr_rates: List[float] = []
    denom_only_fr_rates: List[float] = []
    coverage_rates: List[float] = []
    convergence_diffs: List[float] = []

    delta_biases = {ep: {"di": [], "dn": []}
                    for ep in cfg.node_grid.endpoints}
    delta_coverages = {ep: {"di": [], "dn": []}
                       for ep in cfg.node_grid.endpoints}

    for rep in topic_results:
        nodes = rep["node_results"]
        delta_post = rep.get("delta_posteriors", {})

        cfr = efr = dfr = cov = 0
        conv_sum = conv_n = 0
        n_scorable = 0
        n_cov_scorable = 0

        for nid, nr in nodes.items():
            oracle = nr.get("oracle_meta", {})
            classic = nr.get("classic_meta", {})
            engine = nr.get("engine_propagated", {})
            decision = nr.get("engine_decision", {})
            denom_dec = nr.get("denom_only_decision", {})
            denom = nr.get("node_denom", {})

            oracle_mu = oracle.get("mu")
            if oracle_mu is None or not math.isfinite(oracle_mu):
                continue
            n_scorable += 1

            # ── Classic false reassurance ─────────────────────────────
            c_mu = classic.get("mu")
            c_hi = classic.get("ci_high")
            if c_mu is not None and _fin(c_mu) and _fin(c_hi):
                if c_hi < 0:           # classic says benefit
                    if oracle_mu >= 0:  # oracle says no benefit
                        cfr += 1

            # ── Engine false reassurance ──────────────────────────────
            label = decision.get("label", "")
            if label in ("Recommend", "Consider-benefit"):
                if oracle_mu >= 0:
                    efr += 1

            # ── Denom-only false reassurance ──────────────────────────
            dlabel = denom_dec.get("label", "")
            if dlabel.startswith("Recommend"):
                if oracle_mu >= 0:
                    dfr += 1

            # ── Engine coverage (per-method denominator) ─────────────
            e_lo = engine.get("mu_cri_low")
            e_hi = engine.get("mu_cri_high")
            if e_lo is not None and _fin(e_lo) and _fin(e_hi):
                n_cov_scorable += 1
                if e_lo <= oracle_mu <= e_hi:
                    cov += 1

            # ── Convergence (when silent rate low) ────────────────────
            sr = denom.get("silent_rate", 1.0)
            e_med = engine.get("mu_median")
            if sr < 0.15 and _fin(c_mu) and _fin(e_med):
                conv_sum += abs(e_med - c_mu)
                conv_n += 1

        if n_scorable > 0:
            classic_fr_rates.append(cfr / n_scorable)
            engine_fr_rates.append(efr / n_scorable)
            denom_only_fr_rates.append(dfr / n_scorable)
            coverage_rates.append(cov / n_cov_scorable
                                   if n_cov_scorable > 0 else np.nan)

        if conv_n > 0:
            convergence_diffs.append(conv_sum / conv_n)

        # ── Delta identifiability ─────────────────────────────────────
        ssd = cfg.missingness.silent_shift_delta
        for ep in cfg.node_grid.endpoints:
            s = delta_post.get(ep, {}).get("summary")
            true_d = ssd.delta_by_endpoint.get(ep)
            if s is None or true_d is None:
                continue
            for param, true_val in [("di", true_d.industry),
                                     ("dn", true_d.nonindustry)]:
                est = s.get(f"{param}_mean")
                lo = s.get(f"{param}_cri_low")
                hi = s.get(f"{param}_cri_high")
                if est is not None and _fin(est):
                    delta_biases[ep][param].append(est - true_val)
                if lo is not None and hi is not None and _fin(lo) and _fin(hi):
                    delta_coverages[ep][param].append(
                        int(lo <= true_val <= hi))

    # ── Aggregate ─────────────────────────────────────────────────────
    topic_metrics = {
        "classic_false_reassurance_mean": _safe_mean(classic_fr_rates),
        "engine_false_reassurance_mean": _safe_mean(engine_fr_rates),
        "denom_only_false_reassurance_mean": _safe_mean(denom_only_fr_rates),
        "coverage_engine_mean": _safe_mean(coverage_rates),
        "convergence_mean_abs_diff": _safe_mean(convergence_diffs),
        "n_replications": n_reps,
    }

    delta_metrics = {}
    for ep in cfg.node_grid.endpoints:
        dm = {}
        for param in ("di", "dn"):
            b = delta_biases[ep][param]
            c = delta_coverages[ep][param]
            dm[f"{param}_bias_mean"] = _safe_mean(b)
            dm[f"{param}_bias_sd"] = float(np.std(b)) if b else np.nan
            dm[f"{param}_coverage"] = _safe_mean(c)
        delta_metrics[ep] = dm

    return {"topic_metrics": topic_metrics, "delta_metrics": delta_metrics}


# ── Helpers ───────────────────────────────────────────────────────────────

def _fin(x):
    return x is not None and math.isfinite(x)


def _safe_mean(lst):
    return float(np.nanmean(lst)) if lst else np.nan
