"""Propagate delta posterior to node-level effect estimates.

For each node we sample (di, dn) from the per-endpoint posterior,
compute the compensated effect mu_comp = mu_obs + shift, and derive
posterior summaries (median, 95% CrI, P(benefit), P(harm), P(near-null)).

The CrI includes three uncertainty components:
  1. Delta posterior uncertainty (from grid samples)
  2. Observation uncertainty (SE of observed meta)
  3. Between-study heterogeneity (DL tau-hat) for prediction intervals
"""

import numpy as np
from numpy.random import Generator
from typing import Dict

from .config_schema import TopicConfig


def _estimate_tau_sq(logRR, se):
    """DerSimonian-Laird tau-squared estimator.

    Returns tau^2 >= 0. If k < 2 or Q <= df, returns 0.
    """
    k = len(logRR)
    if k < 2:
        return 0.0
    w = 1.0 / (se ** 2)
    w_sum = w.sum()
    if w_sum < 1e-20:
        return 0.0
    mu_fe = np.sum(w * logRR) / w_sum
    Q = np.sum(w * (logRR - mu_fe) ** 2)
    df = k - 1
    c = w_sum - np.sum(w ** 2) / w_sum
    if c < 1e-20:
        return 0.0
    tau2 = max(0.0, (Q - df) / c)
    return tau2


def propagate(observed_metas: dict, node_denoms_df,
              delta_posteriors: dict, cfg: TopicConfig,
              rng: Generator,
              observed_effects_df=None) -> Dict[str, dict]:
    """Propagate posterior samples to node-level estimates.

    Args:
        observed_metas: node_id -> {mu, se, ci_low, ci_high, k}
        node_denoms_df: DataFrame with node denominator info
        delta_posteriors: endpoint -> posterior dict
        cfg: topic configuration
        rng: seeded RNG
        observed_effects_df: optional DataFrame with per-trial logRR/se
            for tau estimation; if None, uses a default floor

    Returns dict[node_id] -> {
        mu_median, mu_cri_low, mu_cri_high,
        rr_median, rr_cri_low, rr_cri_high,
        p_benefit, p_harm, p_near_null
    }
    """
    prop_cfg = cfg.engine.propagation
    n_samples = prop_cfg.n_posterior_samples
    include_unc = prop_cfg.include_mu_obs_uncertainty
    ssd = cfg.missingness.silent_shift_delta

    denom_dict = {}
    for _, row in node_denoms_df.iterrows():
        denom_dict[row["node_id"]] = row.to_dict()

    # Pre-compute per-node tau from observed effects
    tau_sq_by_node = {}
    if observed_effects_df is not None:
        for nid, grp in observed_effects_df.groupby("node_id"):
            lrr = grp["logRR"].values
            se = grp["se"].values
            valid = np.isfinite(lrr) & np.isfinite(se) & (se > 0)
            if valid.sum() >= 2:
                tau_sq_by_node[nid] = _estimate_tau_sq(lrr[valid], se[valid])

    results = {}

    for nid, meta in observed_metas.items():
        if meta["k"] < 2:
            results[nid] = _empty()
            continue

        denom = denom_dict.get(nid)
        if denom is None:
            results[nid] = _empty()
            continue

        ep = nid.split("|")[2]
        dp = delta_posteriors.get(ep)
        if dp is None:
            results[nid] = _empty()
            continue

        mult = ssd.multiplier_by_endpoint.get(ep, 1.0)
        n_reg = denom["n_registered"]
        n_si = denom["n_silent_industry"]
        n_sn = denom["n_silent_nonindustry"]

        # Build flat posterior for sampling
        posterior_flat = dp["posterior_2d"].ravel()
        p_sum = posterior_flat.sum()
        if p_sum <= 0:
            posterior_flat = np.ones_like(posterior_flat) / len(posterior_flat)
        else:
            posterior_flat = posterior_flat / p_sum

        grid_di = dp["grid_di"]
        grid_dn = dp["grid_dn"]
        di_grid, dn_grid = np.meshgrid(grid_di, grid_dn, indexing="ij")
        di_flat = di_grid.ravel()
        dn_flat = dn_grid.ravel()

        idx = rng.choice(len(posterior_flat), size=n_samples, p=posterior_flat)
        di_s = di_flat[idx]
        dn_s = dn_flat[idx]

        shifts = mult * (n_si * di_s + n_sn * dn_s) / max(n_reg, 1)

        # Observation uncertainty + heterogeneity for prediction interval
        se_obs = meta["se"] if meta["se"] > 0 and np.isfinite(meta["se"]) else 0.0
        tau_sq = tau_sq_by_node.get(nid, 0.0)
        # Prediction variance = SE^2 + tau^2 + model uncertainty floor
        model_unc = prop_cfg.model_unc_floor
        pred_var = se_obs ** 2 + tau_sq + model_unc ** 2

        if include_unc:
            mu_obs_s = rng.normal(meta["mu"], np.sqrt(pred_var),
                                  size=n_samples)
        else:
            mu_obs_s = np.full(n_samples, meta["mu"])

        mu_comp = mu_obs_s + shifts
        rr_comp = np.exp(mu_comp)

        results[nid] = {
            "mu_median": float(np.median(mu_comp)),
            "mu_cri_low": float(np.percentile(mu_comp, 2.5)),
            "mu_cri_high": float(np.percentile(mu_comp, 97.5)),
            "rr_median": float(np.median(rr_comp)),
            "rr_cri_low": float(np.percentile(rr_comp, 2.5)),
            "rr_cri_high": float(np.percentile(rr_comp, 97.5)),
            "p_benefit": float(np.mean(mu_comp < 0)),
            "p_harm": float(np.mean(mu_comp > 0)),
            "p_near_null": float(np.mean(np.abs(mu_comp) <= 0.02)),
        }

    return results


def _empty():
    return {
        "mu_median": np.nan, "mu_cri_low": np.nan, "mu_cri_high": np.nan,
        "rr_median": np.nan, "rr_cri_low": np.nan, "rr_cri_high": np.nan,
        "p_benefit": np.nan, "p_harm": np.nan, "p_near_null": np.nan,
    }
