"""Conservative arbitration: inflate uncertainty, never deflate.

Rules:
  low disagreement  -> use delta engine estimate + its CrI
  mid disagreement  -> inflate delta CrI by factor f (1.25-1.5)
  high disagreement -> inflate by factor g (2.0) + force decision downgrade

CRITICAL: arbitration can ONLY inflate intervals, never shrink them.
"""

import math
from typing import Dict

import numpy as np

from .witness_panel import WitnessEstimate


class ArbitrationResult:
    """Outcome of witness arbitration for a single node."""
    __slots__ = ("mu", "se", "ci_low", "ci_high",
                 "disagreement", "level", "inflation_factor",
                 "decision_downgrade")

    def __init__(self, mu, se, ci_low, ci_high,
                 disagreement, level, inflation_factor,
                 decision_downgrade=False):
        self.mu = mu
        self.se = se
        self.ci_low = ci_low
        self.ci_high = ci_high
        self.disagreement = disagreement
        self.level = level
        self.inflation_factor = inflation_factor
        self.decision_downgrade = decision_downgrade

    def to_dict(self) -> dict:
        return {
            "mu": self.mu, "se": self.se,
            "ci_low": self.ci_low, "ci_high": self.ci_high,
            "disagreement": self.disagreement,
            "level": self.level,
            "inflation_factor": self.inflation_factor,
            "decision_downgrade": self.decision_downgrade,
        }


def arbitrate(panel: Dict[str, WitnessEstimate],
              thresh_low: float = 0.05,
              thresh_high: float = 0.15,
              inflate_mid: float = 1.3,
              inflate_high: float = 2.0) -> ArbitrationResult:
    """Conservative arbitration across three witnesses.

    Uses delta_engine as the base estimate; inflates its interval when
    witnesses disagree.
    """
    mus = []
    for w in panel.values():
        if w.mu is not None and math.isfinite(w.mu):
            mus.append(w.mu)

    if len(mus) < 2:
        # Not enough witnesses; return delta engine as-is
        de = panel.get("delta_engine")
        if de is None:
            return ArbitrationResult(
                mu=np.nan, se=np.nan, ci_low=np.nan, ci_high=np.nan,
                disagreement=np.nan, level="insufficient",
                inflation_factor=1.0, decision_downgrade=True)
        return ArbitrationResult(
            mu=de.mu, se=de.se, ci_low=de.ci_low, ci_high=de.ci_high,
            disagreement=0.0, level="low",
            inflation_factor=1.0, decision_downgrade=False)

    disagreement = float(np.std(mus))

    de = panel["delta_engine"]
    base_mu = de.mu
    base_lo = de.ci_low
    base_hi = de.ci_high
    base_se = de.se

    if disagreement <= thresh_low:
        level = "low"
        factor = 1.0
        downgrade = False
    elif disagreement <= thresh_high:
        level = "mid"
        factor = inflate_mid
        downgrade = False
    else:
        level = "high"
        factor = inflate_high
        downgrade = True

    # Inflate interval around midpoint, then guarantee containment
    if math.isfinite(base_lo) and math.isfinite(base_hi):
        mid = (base_lo + base_hi) / 2
        half_width = (base_hi - base_lo) / 2
        new_half = half_width * factor
        ci_low = min(base_lo, mid - new_half)
        ci_high = max(base_hi, mid + new_half)
    else:
        ci_low = base_lo
        ci_high = base_hi

    se_out = base_se * factor if math.isfinite(base_se) else base_se

    return ArbitrationResult(
        mu=base_mu,
        se=se_out,
        ci_low=ci_low,
        ci_high=ci_high,
        disagreement=disagreement,
        level=level,
        inflation_factor=factor,
        decision_downgrade=downgrade,
    )
