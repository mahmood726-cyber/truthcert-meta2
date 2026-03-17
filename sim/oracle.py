"""Oracle MNAR mechanism (silent-shift delta) and oracle meta-analysis.

The oracle world applies a systematic shift to ALL trial outcomes:
    theta_oracle = theta_true + multiplier(endpoint) * delta(sponsor, endpoint)

This creates MNAR: trials with worse oracle outcomes are more likely to go
silent under the selection model, biasing publication-only meta-analysis.
"""

import numpy as np
import pandas as pd
from numpy.random import Generator

from .config_schema import TopicConfig
from .meta_fixed import fixed_effect
from .utils import clamp, log_rr_and_se


def apply_oracle_shift(trials_df: pd.DataFrame, cfg: TopicConfig,
                       rng: Generator) -> pd.DataFrame:
    """Apply silent-shift delta to create oracle-world outcomes.

    Adds columns:
        theta_oracle, e_treat_oracle, e_control_oracle,
        logRR_oracle, se_oracle
    """
    df = trials_df.copy()
    ssd = cfg.missingness.silent_shift_delta

    n = len(df)
    theta_oracle = np.empty(n)
    e_treat_oracle = np.empty(n, dtype=int)
    e_control_oracle = np.empty(n, dtype=int)
    logRR_oracle = np.empty(n)
    se_oracle = np.empty(n)

    for i in range(n):
        row = df.iloc[i]
        endpoint = row["endpoint"]
        is_ind = row["is_industry"]

        if ssd.enabled:
            mult = ssd.multiplier_by_endpoint.get(endpoint, 1.0)
            delta_entry = ssd.delta_by_endpoint.get(endpoint)
            if delta_entry is not None:
                delta = delta_entry.industry if is_ind else delta_entry.nonindustry
            else:
                delta = 0.0
            theta_o = row["theta_true"] + mult * delta
        else:
            theta_o = row["theta_true"]

        theta_oracle[i] = theta_o

        n_t = row["n_treat"]
        n_c = row["n_control"]
        e_c = row["e_control"]  # keep original control events

        # Treatment arm regenerated from oracle theta
        p_c_est = max(0.001, e_c / n_c) if n_c > 0 else 0.1
        p_t_oracle = clamp(p_c_est * np.exp(theta_o), 0.001, 0.999)
        e_t_o = int(rng.binomial(n_t, p_t_oracle))

        e_treat_oracle[i] = e_t_o
        e_control_oracle[i] = e_c

        lrr, se_ = log_rr_and_se(e_t_o, n_t, e_c, n_c)
        logRR_oracle[i] = lrr
        se_oracle[i] = se_

    df["theta_oracle"] = theta_oracle
    df["e_treat_oracle"] = e_treat_oracle
    df["e_control_oracle"] = e_control_oracle
    df["logRR_oracle"] = logRR_oracle
    df["se_oracle"] = se_oracle

    return df


def oracle_meta_per_node(trials_df: pd.DataFrame) -> dict:
    """Compute oracle meta per node using ALL trials (observed + silent).

    Uses logRR_oracle and se_oracle columns.
    Returns dict mapping node_id -> {mu, se, ci_low, ci_high, k}.
    """
    results = {}
    for nid, grp in trials_df.groupby("node_id"):
        if len(grp) == 0:
            continue
        results[nid] = fixed_effect(grp["logRR_oracle"].values,
                                    grp["se_oracle"].values)
    return results
