"""Witness panel: collect estimates from all three witnesses.

A) Classic FE (publication-only)
B) Delta-engine (Phase 1 posterior propagation)
C) Selection witness (IPW-adjusted)
"""

from typing import Dict, Optional


class WitnessEstimate:
    """A single witness's estimate for a node."""
    __slots__ = ("name", "mu", "se", "ci_low", "ci_high", "k", "extra")

    def __init__(self, name: str, mu: float, se: float,
                 ci_low: float, ci_high: float,
                 k: int = 0, extra: Optional[dict] = None):
        self.name = name
        self.mu = mu
        self.se = se
        self.ci_low = ci_low
        self.ci_high = ci_high
        self.k = k
        self.extra = extra or {}

    def to_dict(self) -> dict:
        return {
            "name": self.name, "mu": self.mu, "se": self.se,
            "ci_low": self.ci_low, "ci_high": self.ci_high,
            "k": self.k, **self.extra,
        }


def build_witness_panel(classic_meta: dict,
                        engine_propagated: dict,
                        selection_result: dict) -> Dict[str, WitnessEstimate]:
    """Assemble the three witnesses for a node.

    Returns dict with keys: "classic", "delta_engine", "selection".
    """
    import math  # local import to avoid circular dependency

    def _safe(d, key, default=float("nan")):
        v = d.get(key, default)
        return v if v is not None else default

    panel = {}

    # A) Classic FE
    panel["classic"] = WitnessEstimate(
        name="classic",
        mu=_safe(classic_meta, "mu"),
        se=_safe(classic_meta, "se"),
        ci_low=_safe(classic_meta, "ci_low"),
        ci_high=_safe(classic_meta, "ci_high"),
        k=int(_safe(classic_meta, "k", 0)),
    )

    # B) Delta engine
    mu_med = _safe(engine_propagated, "mu_median")
    mu_lo = _safe(engine_propagated, "mu_cri_low")
    mu_hi = _safe(engine_propagated, "mu_cri_high")
    # Approximate SE from CrI width / 3.92 (= 2 * 1.96, normal theory).
    # This approximation is used only for ArbitrationResult.se reporting;
    # the arbitration logic itself uses ci_low/ci_high bounds directly.
    se_eng = (mu_hi - mu_lo) / 3.92 if (
        math.isfinite(mu_lo) and math.isfinite(mu_hi)) else float("nan")

    panel["delta_engine"] = WitnessEstimate(
        name="delta_engine",
        mu=mu_med,
        se=se_eng,
        ci_low=mu_lo,
        ci_high=mu_hi,
        extra={
            "p_benefit": _safe(engine_propagated, "p_benefit"),
            "p_harm": _safe(engine_propagated, "p_harm"),
        },
    )

    # C) Selection witness
    panel["selection"] = WitnessEstimate(
        name="selection",
        mu=_safe(selection_result, "mu"),
        se=_safe(selection_result, "se"),
        ci_low=_safe(selection_result, "ci_low"),
        ci_high=_safe(selection_result, "ci_high"),
        k=int(_safe(selection_result, "k", 0)),
        extra={"converged": selection_result.get("converged", False)},
    )

    return panel
