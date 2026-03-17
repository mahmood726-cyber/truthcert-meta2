"""Generate trial-level data from truth parameters via Dirichlet-multinomial."""

import numpy as np
import pandas as pd
from numpy.random import Generator
from scipy.stats import norm

Z_ALPHA_05 = norm.ppf(0.975)

from .config_schema import TopicConfig
from .utils import clamp, log_rr_and_se


def _year_weights() -> np.ndarray:
    """Year sampling weights 2010-2025, higher mass post-2015."""
    w = np.array([1.0] * 6 + [2.0] * 10)  # 2010-2015: 1, 2016-2025: 2
    return w / w.sum()


_YEARS = list(range(2010, 2026))
_YEAR_P = _year_weights()


def generate_trials(cfg: TopicConfig, node_params: dict,
                    rng: Generator) -> pd.DataFrame:
    """Generate trial-level data with binomial events.

    Returns DataFrame with columns:
        trial_id, node_id, phenotype, class_, endpoint, is_industry,
        year_completed, n_treat, n_control, e_treat, e_control,
        theta_true, logRR, se, z, signif_benefit, signif_harm
    """
    tc = cfg.trial_count
    node_ids = list(node_params.keys())
    n_nodes = len(node_ids)

    # Dirichlet-multinomial allocation
    alpha = np.ones(n_nodes) * tc.dispersion
    probs = rng.dirichlet(alpha)
    counts = rng.multinomial(tc.n_trials_total, probs)

    # Enforce minimum trials per node by redistributing from over-allocated nodes
    for i in range(n_nodes):
        if counts[i] < tc.min_trials_per_node:
            deficit = tc.min_trials_per_node - counts[i]
            counts[i] = tc.min_trials_per_node
            # Steal from the largest node(s) to keep total constant
            for _ in range(deficit):
                donor = np.argmax(counts)
                if counts[donor] > tc.min_trials_per_node:
                    counts[donor] -= 1

    ss = cfg.sample_size
    rows = []
    trial_idx = 0

    for node_idx, nid in enumerate(node_ids):
        n_trials_node = int(counts[node_idx])
        parts = nid.split("|")
        phenotype, class_, endpoint = parts[0], parts[1], parts[2]

        np_ = node_params[nid]
        mu = np_["mu"]
        tau = np_["tau"]
        p_c = np_["p_control"]

        for _ in range(n_trials_node):
            trial_id = f"T{trial_idx:05d}"
            trial_idx += 1

            is_industry = bool(rng.random() < cfg.sponsor.industry_rate)

            year_completed = int(rng.choice(_YEARS, p=_YEAR_P))

            # Sample size per arm
            if ss.size_distribution == "lognormal":
                median_n = (ss.n_per_arm[0] + ss.n_per_arm[1]) / 2
                n_arm = int(clamp(
                    rng.lognormal(np.log(median_n), ss.size_sigma),
                    ss.n_per_arm[0],
                    ss.n_per_arm[1],
                ))
            else:  # uniform
                n_arm = int(rng.integers(ss.n_per_arm[0],
                                         ss.n_per_arm[1] + 1))

            n_treat = n_arm
            n_control = n_arm

            # True treatment effect for this trial
            theta_true = float(rng.normal(mu, tau))

            # Generate events
            p_t = clamp(p_c * np.exp(theta_true), 0.001, 0.999)
            e_c = int(rng.binomial(n_control, p_c))
            e_t = int(rng.binomial(n_treat, p_t))

            logRR, se = log_rr_and_se(e_t, n_treat, e_c, n_control)
            z = logRR / se if se > 0 else 0.0

            rows.append({
                "trial_id": trial_id,
                "node_id": nid,
                "phenotype": phenotype,
                "class_": class_,
                "endpoint": endpoint,
                "is_industry": is_industry,
                "year_completed": year_completed,
                "n_treat": n_treat,
                "n_control": n_control,
                "e_treat": e_t,
                "e_control": e_c,
                "theta_true": theta_true,
                "logRR": logRR,
                "se": se,
                "z": z,
                "signif_benefit": z < -Z_ALPHA_05,
                "signif_harm": z > Z_ALPHA_05,
            })

    return pd.DataFrame(rows)
