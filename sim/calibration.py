"""Calibration metrics: coverage and false-alarm rates for the
arbitrated (Meta2) estimates vs. oracle truth.

Coverage uses per-method denominators: nodes without valid intervals
for a given method are excluded from that method's coverage calculation.
"""

import math
from typing import List

import numpy as np


def calibration_metrics(node_results: list) -> dict:
    """Compute calibration for a single replication.

    Each entry in node_results is a dict with:
        oracle_mu, arb_ci_low, arb_ci_high,
        delta_ci_low, delta_ci_high, classic_ci_low, classic_ci_high

    Returns dict with per-method coverage rates using per-method denominators.
    """
    cov_arb = n_arb = 0
    cov_delta = n_delta = 0
    cov_classic = n_classic = 0

    for nr in node_results:
        oracle_mu = nr.get("oracle_mu")
        if oracle_mu is None or not math.isfinite(oracle_mu):
            continue

        # Arbitrated coverage (per-method denominator)
        lo, hi = nr.get("arb_ci_low"), nr.get("arb_ci_high")
        if _fin(lo) and _fin(hi):
            n_arb += 1
            if lo <= oracle_mu <= hi:
                cov_arb += 1

        # Delta engine coverage (per-method denominator)
        lo, hi = nr.get("delta_ci_low"), nr.get("delta_ci_high")
        if _fin(lo) and _fin(hi):
            n_delta += 1
            if lo <= oracle_mu <= hi:
                cov_delta += 1

        # Classic coverage (per-method denominator)
        lo, hi = nr.get("classic_ci_low"), nr.get("classic_ci_high")
        if _fin(lo) and _fin(hi):
            n_classic += 1
            if lo <= oracle_mu <= hi:
                cov_classic += 1

    return {
        "coverage_arb": cov_arb / n_arb if n_arb > 0 else np.nan,
        "coverage_delta": cov_delta / n_delta if n_delta > 0 else np.nan,
        "coverage_classic": cov_classic / n_classic if n_classic > 0 else np.nan,
        "n_arb": n_arb,
        "n_delta": n_delta,
        "n_classic": n_classic,
    }


def aggregate_calibration(rep_calibrations: List[dict]) -> dict:
    """Average calibration across replications."""
    keys = ["coverage_arb", "coverage_delta", "coverage_classic"]
    out = {}
    for k in keys:
        vals = [r[k] for r in rep_calibrations if _fin(r.get(k))]
        out[k] = float(np.mean(vals)) if vals else np.nan
    out["n_reps"] = len(rep_calibrations)
    return out


def _fin(x):
    return x is not None and math.isfinite(x)
