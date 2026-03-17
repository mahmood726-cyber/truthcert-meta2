"""Utility functions for the simulation suite."""

import numpy as np


def sigmoid(x):
    """Numerically stable sigmoid function."""
    x = np.asarray(x, dtype=float)
    x = np.clip(x, -500, 500)
    return np.where(x >= 0,
                    1.0 / (1.0 + np.exp(-x)),
                    np.exp(x) / (1.0 + np.exp(x)))


def logit(p):
    """Logit transform with clipping to avoid infinities."""
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return np.log(p / (1 - p))


def clamp(x, lo, hi):
    """Clamp a scalar to [lo, hi]."""
    return max(lo, min(hi, x))


def log_rr_and_se(e_t, n_t, e_c, n_c, cc=0.5):
    """Compute log risk ratio and its SE with continuity correction.

    Applies 0.5 continuity correction when any cell is 0 or equals its margin.
    Returns (logRR, SE).
    """
    need_cc = (e_t == 0 or e_c == 0 or e_t == n_t or e_c == n_c)
    if need_cc:
        e_t_adj = e_t + cc
        e_c_adj = e_c + cc
        n_t_adj = n_t + 2 * cc
        n_c_adj = n_c + 2 * cc
    else:
        e_t_adj = float(e_t)
        e_c_adj = float(e_c)
        n_t_adj = float(n_t)
        n_c_adj = float(n_c)

    p_t = e_t_adj / n_t_adj
    p_c = e_c_adj / n_c_adj
    lrr = np.log(p_t / p_c)
    se = np.sqrt(1.0 / e_t_adj - 1.0 / n_t_adj + 1.0 / e_c_adj - 1.0 / n_c_adj)
    return float(lrr), float(se)
