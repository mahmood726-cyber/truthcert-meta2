"""Fixed-effect (inverse-variance) meta-analysis."""

import numpy as np
from scipy.stats import norm

Z_ALPHA_05 = norm.ppf(0.975)  # 1.959964...


def fixed_effect(logRR: np.ndarray, se: np.ndarray) -> dict:
    """Inverse-variance weighted fixed-effect pooling.

    Args:
        logRR: array of log risk ratios
        se:    array of standard errors

    Returns dict with keys: mu, se, ci_low, ci_high, k
    """
    logRR = np.asarray(logRR, dtype=float)
    se = np.asarray(se, dtype=float)

    valid = np.isfinite(logRR) & np.isfinite(se) & (se > 0)
    logRR = logRR[valid]
    se = se[valid]
    k = len(logRR)

    if k == 0:
        return {"mu": np.nan, "se": np.nan,
                "ci_low": np.nan, "ci_high": np.nan, "k": 0}

    w = 1.0 / (se ** 2)
    mu = float(np.sum(w * logRR) / np.sum(w))
    se_mu = float(np.sqrt(1.0 / np.sum(w)))
    ci_low = mu - Z_ALPHA_05 * se_mu
    ci_high = mu + Z_ALPHA_05 * se_mu

    return {"mu": mu, "se": se_mu,
            "ci_low": ci_low, "ci_high": ci_high, "k": int(k)}


def random_effects_dl(logRR: np.ndarray, se: np.ndarray) -> dict:
    """DerSimonian-Laird random-effects meta-analysis.

    Returns dict with keys: mu, se, ci_low, ci_high, k, tau2, I2
    """
    logRR = np.asarray(logRR, dtype=float)
    se = np.asarray(se, dtype=float)

    valid = np.isfinite(logRR) & np.isfinite(se) & (se > 0)
    logRR = logRR[valid]
    se = se[valid]
    k = len(logRR)

    if k == 0:
        return {"mu": np.nan, "se": np.nan,
                "ci_low": np.nan, "ci_high": np.nan,
                "k": 0, "tau2": 0.0, "I2": 0.0}

    if k == 1:
        mu = float(logRR[0])
        se_mu = float(se[0])
        return {"mu": mu, "se": se_mu,
                "ci_low": mu - Z_ALPHA_05 * se_mu,
                "ci_high": mu + Z_ALPHA_05 * se_mu,
                "k": 1, "tau2": 0.0, "I2": 0.0}

    w = 1.0 / (se ** 2)
    w_sum = w.sum()
    mu_fe = np.sum(w * logRR) / w_sum
    Q = float(np.sum(w * (logRR - mu_fe) ** 2))
    df = k - 1
    c = float(w_sum - np.sum(w ** 2) / w_sum)

    tau2 = max(0.0, (Q - df) / c) if c > 1e-20 else 0.0
    I2 = max(0.0, (Q - df) / Q * 100) if Q > df else 0.0

    w_re = 1.0 / (se ** 2 + tau2)
    w_re_sum = w_re.sum()
    mu_re = float(np.sum(w_re * logRR) / w_re_sum)
    se_re = float(np.sqrt(1.0 / w_re_sum))
    ci_low = mu_re - Z_ALPHA_05 * se_re
    ci_high = mu_re + Z_ALPHA_05 * se_re

    return {"mu": mu_re, "se": se_re,
            "ci_low": ci_low, "ci_high": ci_high,
            "k": int(k), "tau2": float(tau2), "I2": float(I2)}


def i_squared(logRR: np.ndarray, se: np.ndarray) -> float:
    """Cochran Q-based I-squared heterogeneity statistic (%)."""
    logRR = np.asarray(logRR, dtype=float)
    se = np.asarray(se, dtype=float)
    valid = np.isfinite(logRR) & np.isfinite(se) & (se > 0)
    logRR = logRR[valid]
    se = se[valid]
    k = len(logRR)

    if k <= 1:
        return 0.0

    w = 1.0 / (se ** 2)
    mu = np.sum(w * logRR) / np.sum(w)
    Q = float(np.sum(w * (logRR - mu) ** 2))
    df = k - 1

    if Q <= df:
        return 0.0
    return float(max(0.0, (Q - df) / Q * 100))
