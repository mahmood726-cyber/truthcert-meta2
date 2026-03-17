"""Bias decomposition: three-component bias profile per node.

Decomposes missingness into:
  1) silent_trial_rate       -- trial never appeared anywhere
  2) endpoint_missing_rate   -- results posted but this endpoint absent
  3) publication_missing_rate -- not formally published
"""

from typing import Dict

from pydantic import BaseModel


class BiasProfile(BaseModel):
    """Three-rate bias decomposition for a single node."""
    silent_trial_rate: float       # 1 - observed_any / registered
    endpoint_missing_rate: float   # results_posted but endpoint absent
    publication_missing_rate: float  # observed_any but not published
    industry_fraction: float       # share of industry-sponsored trials
    n_registered: int


def compute_bias_profile(node_denom: dict) -> BiasProfile:
    """Derive a BiasProfile from node denominator data."""
    n_reg = node_denom.get("n_registered", 0)
    n_obs = node_denom.get("n_observed_any", 0)
    n_rp = node_denom.get("n_results_posted", 0)
    n_pub = node_denom.get("n_published", 0)
    ep_rate = node_denom.get("endpoint_report_rate", 1.0)
    ind_rate = node_denom.get("industry_rate", 0.0)

    silent_rate = 1 - n_obs / n_reg if n_reg > 0 else 0.0

    # Endpoint missing: trials that posted results but didn't report endpoint
    if n_rp > 0:
        ep_missing = 1.0 - ep_rate
    else:
        ep_missing = 0.0

    # Publication missing: observed but not formally published
    if n_obs > 0:
        pub_missing = 1.0 - n_pub / n_obs
    else:
        pub_missing = 0.0

    return BiasProfile(
        silent_trial_rate=silent_rate,
        endpoint_missing_rate=ep_missing,
        publication_missing_rate=pub_missing,
        industry_fraction=ind_rate,
        n_registered=n_reg,
    )


def compute_bias_profiles(node_denoms_df) -> Dict[str, BiasProfile]:
    """Compute BiasProfile for every node."""
    profiles = {}
    for _, row in node_denoms_df.iterrows():
        nid = row["node_id"]
        profiles[nid] = compute_bias_profile(row.to_dict())
    return profiles
