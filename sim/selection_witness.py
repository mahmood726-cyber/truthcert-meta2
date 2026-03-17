"""Selection witness: publication-bias-adjusted pooled estimate.

Simple inverse-probability weighting (IPW) approach:
  1) Estimate publication probability as a function of SE and significance.
  2) Weight each observed study by 1/P(published) in the fixed-effect pool.
This produces mu_sel, se_sel that account for selection on significance.
"""

import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm

from .utils import sigmoid, logit

Z_ALPHA_05 = norm.ppf(0.975)


def selection_witness(logRR: np.ndarray, se: np.ndarray,
                      signif_benefit: np.ndarray,
                      signif_harm: np.ndarray) -> dict:
    """Compute selection-adjusted pooled effect via IPW.

    Args:
        logRR: observed log risk ratios
        se: observed standard errors
        signif_benefit: boolean array
        signif_harm: boolean array

    Returns dict with keys: mu, se, ci_low, ci_high, k, converged
    """
    logRR = np.asarray(logRR, dtype=float)
    se = np.asarray(se, dtype=float)
    signif_benefit = np.asarray(signif_benefit, dtype=float)
    signif_harm = np.asarray(signif_harm, dtype=float)

    valid = np.isfinite(logRR) & np.isfinite(se) & (se > 0)
    logRR = logRR[valid]
    se = se[valid]
    signif_benefit = signif_benefit[valid]
    signif_harm = signif_harm[valid]
    k = len(logRR)

    if k < 3:
        # Not enough data for selection modelling, fall back to FE
        if k == 0:
            return {"mu": np.nan, "se": np.nan,
                    "ci_low": np.nan, "ci_high": np.nan,
                    "k": 0, "converged": False}
        w = 1.0 / se ** 2
        mu = float(np.sum(w * logRR) / np.sum(w))
        se_mu = float(np.sqrt(1.0 / np.sum(w)))
        return {"mu": mu, "se": se_mu,
                "ci_low": mu - Z_ALPHA_05 * se_mu,
                "ci_high": mu + Z_ALPHA_05 * se_mu,
                "k": k, "converged": False}

    # Standardise SE for numerical stability
    se_mean = se.mean()
    se_std = se.std()
    if se_std < 1e-8:
        se_std = 1.0
    se_z = (se - se_mean) / se_std

    # Fit logistic selection model: logit(p_select) = a + b*inv_se_z + c*sig_ben + d*sig_harm
    # Use maximum likelihood with regularization on ALL parameters including
    # intercept to prevent degeneracy (intercept-only collapse to p_sel -> 1).
    # Clamp reciprocal to [-20, 20] to avoid extreme values near se_z = 0.
    inv_se_z = np.clip(1.0 / (se_z + 1e-6), -20.0, 20.0)

    def neg_ll(params):
        a, b, c, d = params
        lp = a + b * inv_se_z + c * signif_benefit + d * signif_harm
        p_sel = sigmoid(lp)
        p_sel = np.clip(p_sel, 0.01, 0.99)
        # Regularize ALL parameters including intercept (prevents a -> +inf)
        reg = 0.1 * a ** 2 + 0.01 * (b ** 2 + c ** 2 + d ** 2)
        return -np.sum(np.log(p_sel)) + reg

    try:
        res = minimize(neg_ll, x0=[0.0, 0.0, 0.5, 0.0], method="Nelder-Mead",
                       options={"maxiter": 500, "xatol": 1e-6})
        converged = res.success
        a, b, c, d = res.x
    except Exception:
        converged = False
        a, b, c, d = 0.0, 0.0, 0.0, 0.0

    # Compute IPW weights (use same clamped inv_se_z as during fitting)
    lp = a + b * inv_se_z + c * signif_benefit + d * signif_harm
    p_sel = sigmoid(lp)
    p_sel = np.clip(p_sel, 0.05, 0.99)  # floor to prevent extreme weights

    ipw = 1.0 / p_sel
    # Combine with precision weights
    w = ipw / (se ** 2)
    w_sum = w.sum()

    if w_sum < 1e-12:
        # Fall back to simple FE
        w = 1.0 / se ** 2
        w_sum = w.sum()

    mu = float(np.sum(w * logRR) / w_sum)
    # Horvitz-Thompson sandwich SE for IPW-weighted estimate
    se_mu = float(np.sqrt(np.sum(w ** 2 * se ** 2) / w_sum ** 2))
    ci_low = mu - Z_ALPHA_05 * se_mu
    ci_high = mu + Z_ALPHA_05 * se_mu

    return {"mu": mu, "se": se_mu,
            "ci_low": ci_low, "ci_high": ci_high,
            "k": k, "converged": converged}
