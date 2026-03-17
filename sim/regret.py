"""Decision-regret scoring.

regret = w_fp * I(recommend when oracle null/harm)
       + w_fn * I(block when oracle benefit)

Compare regret across: classic, phase1-delta, meta2-arbitrated.
"""

import math
from typing import List

import numpy as np


def compute_regret(node_results: list,
                   w_fp: float = 1.0,
                   w_fn: float = 1.0,
                   w_research: float = 0.5) -> dict:
    """Compute regret for a single replication.

    Each entry in node_results is a dict with:
        oracle_mu,
        classic_decision, delta_decision, arb_decision

    Decisions are strings: "Recommend", "Consider-benefit", "Consider-harm",
                          "Research", "DoNot", "Insufficient", etc.

    Args:
        w_fp: weight for false positive (recommend when oracle says no benefit)
        w_fn: weight for false negative (block when oracle says benefit)
        w_research: multiplier on w_fn for "Research" decisions (default 0.5),
            reflecting that deferring for more data is less costly than
            a definitive "DoNot" when the oracle says benefit.

    Returns per-method regret.
    """
    regret_classic = regret_delta = regret_arb = 0.0
    n = 0

    for nr in node_results:
        oracle_mu = nr.get("oracle_mu")
        if oracle_mu is None or not math.isfinite(oracle_mu):
            continue
        n += 1

        oracle_benefit = oracle_mu < 0  # logRR < 0 = benefit

        for method, dec_key in [("classic", "classic_decision"),
                                ("delta", "delta_decision"),
                                ("arb", "arb_decision")]:
            dec = nr.get(dec_key, "Insufficient")

            # False positive: recommend benefit when oracle says no benefit
            is_benefit_rec = dec in ("Recommend", "Consider-benefit",
                                     "Recommend-denom")
            if is_benefit_rec and not oracle_benefit:
                if method == "classic":
                    regret_classic += w_fp
                elif method == "delta":
                    regret_delta += w_fp
                else:
                    regret_arb += w_fp

            # False negative: block/DoNot/Consider-harm when oracle says benefit
            # "Research" incurs reduced penalty (w_research * w_fn) since it
            # acknowledges uncertainty rather than making a definitive block.
            if dec in ("DoNot", "Consider-harm") and oracle_benefit:
                penalty = w_fn
            elif dec == "Research" and oracle_benefit:
                penalty = w_fn * w_research
            else:
                penalty = 0.0

            if penalty > 0:
                if method == "classic":
                    regret_classic += penalty
                elif method == "delta":
                    regret_delta += penalty
                else:
                    regret_arb += penalty

    if n == 0:
        return {"regret_classic": np.nan,
                "regret_delta": np.nan,
                "regret_arb": np.nan,
                "n_scorable": 0}

    return {
        "regret_classic": regret_classic / n,
        "regret_delta": regret_delta / n,
        "regret_arb": regret_arb / n,
        "n_scorable": n,
    }


def aggregate_regret(rep_regrets: List[dict]) -> dict:
    """Average regret across replications."""
    keys = ["regret_classic", "regret_delta", "regret_arb"]
    out = {}
    for k in keys:
        vals = [r[k] for r in rep_regrets
                if r.get("n_scorable", 0) > 0 and math.isfinite(r.get(k, float("nan")))]
        out[k] = float(np.mean(vals)) if vals else np.nan
    out["n_reps"] = len(rep_regrets)
    return out
