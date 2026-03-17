"""Decision rules: Recommend / Consider / Research / DoNot."""

import math

from .config_schema import TopicConfig


def decide(propagated_node: dict, node_denom: dict,
           cfg: TopicConfig) -> dict:
    """Apply decision rules to a single propagated node.

    Returns {"label": str, "reason": str}.
    """
    rules = cfg.engine.decision_rule
    silent_rate = node_denom.get("silent_rate", 0.0)

    p_benefit = propagated_node.get("p_benefit")
    p_harm = propagated_node.get("p_harm")
    rr_cri_high = propagated_node.get("rr_cri_high")

    # Guard against NaN / missing
    vals = [v for v in [p_benefit, p_harm, rr_cri_high] if v is not None]
    if not vals or any(math.isnan(v) for v in vals):
        return {"label": "Insufficient",
                "reason": "Missing or NaN propagated estimates"}

    # 1) Recommend
    rec = rules.recommend
    if (p_benefit >= rec.p_benefit
            and rr_cri_high < rec.upper
            and silent_rate <= rec.silent_rate_max):
        return {
            "label": "Recommend",
            "reason": (f"p_benefit={p_benefit:.2f} upper={rr_cri_high:.3f} "
                       f"silent={silent_rate:.2f}"),
        }

    # 2) Consider
    con = rules.consider
    if ((p_benefit >= con.p_benefit or p_harm >= con.p_harm)
            and silent_rate <= con.silent_rate_max):
        direction = "benefit" if p_benefit >= con.p_benefit else "harm"
        return {
            "label": f"Consider-{direction}",
            "reason": (f"p_ben={p_benefit:.2f} p_harm={p_harm:.2f} "
                       f"silent={silent_rate:.2f}"),
        }

    # 3) Research
    res = rules.research
    if silent_rate >= res.silent_rate_min:
        return {
            "label": "Research",
            "reason": f"silent_rate={silent_rate:.2f} >= {res.silent_rate_min}",
        }

    # 4) DoNot
    return {
        "label": "DoNot",
        "reason": (f"No criteria met: p_ben={p_benefit:.2f} "
                   f"silent={silent_rate:.2f}"),
    }


def decide_denom_only(node_denom: dict) -> dict:
    """Ablation: decision using only denominator silent-rate thresholds."""
    sr = node_denom.get("silent_rate", 0.0)
    if sr >= 0.40:
        return {"label": "Research",
                "reason": f"denom_only: silent_rate={sr:.2f}"}
    if sr >= 0.15:
        return {"label": "Consider-denom",
                "reason": f"denom_only: silent_rate={sr:.2f}"}
    return {"label": "Recommend-denom",
            "reason": f"denom_only: silent_rate={sr:.2f}"}
