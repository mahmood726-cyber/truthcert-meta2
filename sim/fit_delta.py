"""Bayesian delta posterior fit via coherence-likelihood grid search.

For each endpoint, we estimate (di, dn) -- the effect shift attributable
to silent industry and non-industry trials respectively -- by minimising
the weighted within-group variance of compensated node effects across a
discrete grid, tempered by half-normal priors.
"""

from typing import Dict

import numpy as np

from .config_schema import TopicConfig


def fit_delta(observed_metas: dict, node_denoms_df,
              cfg: TopicConfig) -> Dict[str, dict]:
    """Fit delta (di, dn) posterior per endpoint.

    Args:
        observed_metas: node_id -> {mu, se, ci_low, ci_high, k}
        node_denoms_df: DataFrame with node denominator info
        cfg: topic configuration

    Returns dict[endpoint] -> {
        grid_di, grid_dn, posterior_2d,
        summary: {di_mean, di_median, di_map, di_cri_low, di_cri_high,
                  dn_mean, dn_median, dn_map, dn_cri_low, dn_cri_high}
    }
    """
    db = cfg.engine.delta_bayes
    grid_cfg = db.grid
    prior_cfg = db.prior
    T = db.temperature_T
    grouping = db.grouping
    ssd = cfg.missingness.silent_shift_delta

    grid_di = np.arange(0, grid_cfg.di_max + grid_cfg.step / 2, grid_cfg.step)
    grid_dn = np.arange(0, grid_cfg.dn_max + grid_cfg.step / 2, grid_cfg.step)

    # Index denominators
    denom_dict = {}
    for _, row in node_denoms_df.iterrows():
        denom_dict[row["node_id"]] = row.to_dict()

    results = {}
    for ep in cfg.node_grid.endpoints:
        # Gather nodes for this endpoint with k_obs >= 2
        ep_nodes = []
        for nid, meta in observed_metas.items():
            if nid.split("|")[2] == ep and meta["k"] >= 2:
                denom = denom_dict.get(nid)
                if denom is not None:
                    ep_nodes.append((nid, meta, denom))

        if len(ep_nodes) == 0:
            posterior = np.ones((len(grid_di), len(grid_dn)))
            posterior /= posterior.sum()
            results[ep] = _build_result(grid_di, grid_dn, posterior)
            continue

        mult = ssd.multiplier_by_endpoint.get(ep, 1.0)

        n_di = len(grid_di)
        n_dn = len(grid_dn)
        log_post = np.full((n_di, n_dn), -np.inf)

        for i in range(n_di):
            di = grid_di[i]
            for j in range(n_dn):
                dn = grid_dn[j]

                # Constraint: di >= dn
                if di < dn - 1e-12:
                    continue

                # Compute compensated effects
                mu_comps = []
                se_obs_list = []
                group_labels = []

                for nid, meta, denom in ep_nodes:
                    mu_obs = meta["mu"]
                    se_obs = meta["se"]
                    n_reg = denom["n_registered"]
                    n_si = denom["n_silent_industry"]
                    n_sn = denom["n_silent_nonindustry"]

                    if n_reg == 0:
                        continue

                    shift = mult * (n_si * di + n_sn * dn) / n_reg
                    mu_comp = mu_obs + shift

                    mu_comps.append(mu_comp)
                    se_obs_list.append(se_obs)

                    parts = nid.split("|")
                    if grouping == "class":
                        group_labels.append(parts[1])
                    elif grouping == "phenotype":
                        group_labels.append(parts[0])
                    else:  # endpoint
                        group_labels.append(ep)

                if len(mu_comps) < 2:
                    log_post[i, j] = 0.0
                    continue

                # Weighted within-group variance objective
                objective = 0.0
                for g in set(group_labels):
                    g_idx = [idx for idx, gl in enumerate(group_labels)
                             if gl == g]
                    if len(g_idx) < 2:
                        continue
                    g_mu = np.array([mu_comps[idx] for idx in g_idx])
                    g_w = np.array([1.0 / se_obs_list[idx] ** 2
                                    for idx in g_idx])
                    g_w_sum = g_w.sum()
                    if g_w_sum < 1e-20:
                        continue
                    g_mean = np.sum(g_w * g_mu) / g_w_sum
                    objective += np.sum(g_w * (g_mu - g_mean) ** 2)

                log_post[i, j] = -objective / max(T, 1e-6)

        # Add log half-normal priors
        for i, di in enumerate(grid_di):
            log_post[i, :] += -di ** 2 / (2 * prior_cfg.sigma_industry ** 2)
        for j, dn in enumerate(grid_dn):
            log_post[:, j] += -dn ** 2 / (2 * prior_cfg.sigma_nonindustry ** 2)

        # Normalise
        finite_mask = np.isfinite(log_post)
        if finite_mask.any():
            log_post -= np.max(log_post[finite_mask])
        posterior = np.exp(log_post)
        posterior[~finite_mask] = 0.0
        total = posterior.sum()
        if total > 0:
            posterior /= total
        else:
            posterior = np.ones_like(posterior)
            posterior /= posterior.size

        results[ep] = _build_result(grid_di, grid_dn, posterior)

    return results


# ── Posterior summary helpers ─────────────────────────────────────────────

def _build_result(grid_di, grid_dn, posterior):
    marg_di = posterior.sum(axis=1)
    if marg_di.sum() > 0:
        marg_di /= marg_di.sum()

    marg_dn = posterior.sum(axis=0)
    if marg_dn.sum() > 0:
        marg_dn /= marg_dn.sum()

    return {
        "grid_di": grid_di,
        "grid_dn": grid_dn,
        "posterior_2d": posterior,
        "summary": {
            "di_mean": float(np.sum(grid_di * marg_di)),
            "di_median": _weighted_median(grid_di, marg_di),
            "di_map": float(grid_di[np.argmax(marg_di)]),
            "di_cri_low": _cri(grid_di, marg_di, 0.95)[0],
            "di_cri_high": _cri(grid_di, marg_di, 0.95)[1],
            "dn_mean": float(np.sum(grid_dn * marg_dn)),
            "dn_median": _weighted_median(grid_dn, marg_dn),
            "dn_map": float(grid_dn[np.argmax(marg_dn)]),
            "dn_cri_low": _cri(grid_dn, marg_dn, 0.95)[0],
            "dn_cri_high": _cri(grid_dn, marg_dn, 0.95)[1],
        },
    }


def _weighted_median(vals, weights):
    idx = np.argsort(vals)
    sv, sw = vals[idx], weights[idx]
    cs = np.cumsum(sw)
    total = cs[-1]
    if total == 0:
        return float(sv[0])
    i = np.searchsorted(cs, total / 2)
    return float(sv[min(i, len(sv) - 1)])


def _cri(vals, weights, level=0.95):
    """Equal-tailed credible interval."""
    alpha = 1 - level
    idx = np.argsort(vals)
    sv, sw = vals[idx], weights[idx]
    cs = np.cumsum(sw)
    total = cs[-1]
    if total == 0:
        return (float(sv[0]), float(sv[-1]))
    lo = np.searchsorted(cs, total * alpha / 2)
    hi = np.searchsorted(cs, total * (1 - alpha / 2))
    lo = min(lo, len(sv) - 1)
    hi = min(hi, len(sv) - 1)
    return (float(sv[lo]), float(sv[hi]))
