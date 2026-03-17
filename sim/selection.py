"""Two-stage MNAR selection mechanism + endpoint reporting.

Selection acts on features derived from the *original* trial outcomes
(theta_true-based z, SE, significance flags).  The *observed* effect
values will come from the oracle world (logRR_oracle, se_oracle).
"""

import numpy as np
import pandas as pd
from numpy.random import Generator

from .config_schema import TopicConfig
from .utils import sigmoid, logit


def apply_selection(trials_df: pd.DataFrame, cfg: TopicConfig,
                    rng: Generator) -> pd.DataFrame:
    """Apply two-stage selection + optional endpoint reporting.

    Adds columns:
        results_posted, published, endpoint_reported,
        observed_any, silent_trial, silent_for_endpoint
    """
    df = trials_df.copy()
    miss = cfg.missingness
    n = len(df)

    # ── Feature vectors (from original / theta_true outcomes) ─────────
    se_vals = df["se"].values.astype(float)
    se_mean = se_vals.mean()
    se_std = se_vals.std()
    if se_std < 1e-12:
        se_std = 1.0
    se_z = (se_vals - se_mean) / se_std  # standardised SE

    industry = df["is_industry"].astype(float).values
    sig_ben = df["signif_benefit"].astype(float).values
    sig_harm = df["signif_harm"].astype(float).values
    post2015 = (df["year_completed"] >= 2016).astype(float).values

    # ── Stage 1: results_posted ───────────────────────────────────────
    rp = miss.results_posting
    lp = logit(rp.base_rate) * np.ones(n)
    lp += rp.coef.get("industry", 0) * industry
    lp += rp.coef.get("signif_benefit", 0) * sig_ben
    lp += rp.coef.get("signif_harm", 0) * sig_harm
    lp += rp.coef.get("se", 0) * se_z
    lp += rp.coef.get("post2015", 0) * post2015
    results_posted = rng.random(n) < sigmoid(lp)

    # ── Stage 2: published ────────────────────────────────────────────
    pub = miss.publication
    lp2 = logit(pub.base_rate) * np.ones(n)
    lp2 += pub.coef.get("industry", 0) * industry
    lp2 += pub.coef.get("signif_benefit", 0) * sig_ben
    lp2 += pub.coef.get("signif_harm", 0) * sig_harm
    lp2 += pub.coef.get("se", 0) * se_z
    lp2 += pub.coef.get("post2015", 0) * post2015
    lp2 += pub.coef.get("results_posted", 0) * results_posted.astype(float)
    published = rng.random(n) < sigmoid(lp2)

    # ── Stage 3: endpoint-level reporting (conditional on results) ────
    er = miss.endpoint_reporting
    endpoint_reported = np.zeros(n, dtype=bool)

    if er.enabled:
        for ep in df["endpoint"].unique():
            mask = (df["endpoint"].values == ep) & results_posted
            if not mask.any():
                continue
            base = er.base_rate_by_endpoint.get(ep, 0.8)
            lp3 = logit(base) * np.ones(mask.sum())
            lp3 += er.coef.get("industry", 0) * industry[mask]
            lp3 += er.coef.get("signif_benefit", 0) * sig_ben[mask]
            lp3 += er.coef.get("se", 0) * se_z[mask]
            endpoint_reported[mask] = rng.random(mask.sum()) < sigmoid(lp3)
    else:
        # If endpoint reporting is disabled, treat all results-posted as reported
        endpoint_reported = results_posted.copy()

    # ── Derived flags ─────────────────────────────────────────────────
    observed_any = results_posted | published
    silent_trial = ~observed_any
    silent_for_endpoint = ~(endpoint_reported | published)

    df["results_posted"] = results_posted
    df["published"] = published
    df["endpoint_reported"] = endpoint_reported
    df["observed_any"] = observed_any
    df["silent_trial"] = silent_trial
    df["silent_for_endpoint"] = silent_for_endpoint

    return df
