"""Build observed world: observed effect rows + node denominator tables.

Observed effects use *oracle-generated* logRR/se (so the MNAR shift is
baked into the data the engine and classic meta-analysis actually see).
"""

import numpy as np
import pandas as pd

from .config_schema import TopicConfig


def build_observed_world(trials_df: pd.DataFrame,
                         cfg: TopicConfig):
    """Construct observed_effects and node_denoms from the selected trials.

    Returns (observed_effects: DataFrame, node_denoms: DataFrame).
    """
    df = trials_df

    # ── Observed effects: (results_posted AND endpoint_reported) OR published
    # Published trials have endpoint data from the journal article.
    obs_mask = (df["results_posted"].values & df["endpoint_reported"].values) | df["published"].values

    observed_effects = df.loc[obs_mask, [
        "trial_id", "node_id", "endpoint", "is_industry",
        "logRR_oracle", "se_oracle",
        "n_treat", "n_control",
        "e_treat_oracle", "e_control_oracle",
        "results_posted", "published",
    ]].copy()

    observed_effects.rename(columns={
        "logRR_oracle": "logRR",
        "se_oracle": "se",
        "e_treat_oracle": "e_treat",
        "e_control_oracle": "e_control",
    }, inplace=True)

    observed_effects["has_results"] = True
    observed_effects["has_pub"] = df.loc[obs_mask, "published"].values

    # ── Node denominators ─────────────────────────────────────────────
    node_rows = []
    for nid, grp in df.groupby("node_id"):
        n_reg = len(grp)
        n_rp = int(grp["results_posted"].sum())
        n_pub = int(grp["published"].sum())
        n_obs = int(grp["observed_any"].sum())
        n_silent = n_reg - n_obs
        silent_rate = n_silent / n_reg if n_reg > 0 else 0.0

        ind_mask = grp["is_industry"]
        n_ind = int(ind_mask.sum())
        n_silent_ind = int((grp["silent_trial"] & ind_mask).sum())
        n_silent_non = int((grp["silent_trial"] & ~ind_mask).sum())
        ind_rate = n_ind / n_reg if n_reg > 0 else 0.0

        ep_reported = int(grp["endpoint_reported"].sum())
        ep_report_rate = ep_reported / n_reg if n_reg > 0 else 0.0

        node_rows.append({
            "node_id": nid,
            "n_registered": n_reg,
            "n_results_posted": n_rp,
            "n_published": n_pub,
            "n_observed_any": n_obs,
            "n_silent": n_silent,
            "silent_rate": silent_rate,
            "industry_rate": ind_rate,
            "n_silent_industry": n_silent_ind,
            "n_silent_nonindustry": n_silent_non,
            "endpoint_report_rate": ep_report_rate,
        })

    node_denoms = pd.DataFrame(node_rows)
    return observed_effects, node_denoms
