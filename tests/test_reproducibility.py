"""Test deterministic reproducibility for Meta2."""

import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sim.config_schema import TopicConfig
from sim.run_suite import run_topic


def _make_test_topic() -> TopicConfig:
    return TopicConfig(**{
        "topic_id": "T_repro2",
        "label": "Meta2 Repro",
        "node_grid": {"phenotypes": ["P1"], "classes": ["C1"],
                      "endpoints": ["E1"]},
        "trial_count": {"n_trials_total": 20, "min_trials_per_node": 5,
                        "dispersion": 1.0},
        "sponsor": {"industry_rate": 0.5},
        "truth": {"mu_global": -0.15, "node_effect_structure": "smooth",
                  "mu_node_sd": 0.10, "tau_base": 0.08, "tau_sd": 0.02,
                  "discontinuity": {"enabled": False}},
        "baseline_risk": {"control_event_rate": {"E1": [0.1, 0.3]}},
        "sample_size": {"n_per_arm": [50, 200],
                        "size_distribution": "uniform"},
        "missingness": {
            "results_posting": {"base_rate": 0.70,
                                "coef": {"industry": 0.2, "signif_benefit": 0.3,
                                         "signif_harm": -0.2, "se": -0.1,
                                         "post2015": 0.2}},
            "publication": {"base_rate": 0.60,
                            "coef": {"industry": 0.1, "signif_benefit": 0.5,
                                     "signif_harm": 0.2, "se": -0.3,
                                     "post2015": 0.1, "results_posted": 0.3}},
            "endpoint_reporting": {"enabled": False,
                                   "base_rate_by_endpoint": {"E1": 0.9},
                                   "coef": {"industry": 0.1, "signif_benefit": 0.2,
                                            "se": -0.1}},
            "silent_shift_delta": {"enabled": True,
                                   "delta_by_endpoint": {"E1": {"industry": 0.05,
                                                                "nonindustry": 0.02}},
                                   "constraint": "industry_ge_nonindustry",
                                   "multiplier_by_endpoint": {"E1": 1.0}},
        },
        "engine": {
            "delta_bayes": {"grid": {"di_max": 0.3, "dn_max": 0.2, "step": 0.05},
                            "prior": {"type": "half_normal", "sigma_industry": 0.2,
                                      "sigma_nonindustry": 0.15},
                            "temperature_T": 1.0, "grouping": "endpoint"},
            "propagation": {"n_posterior_samples": 500,
                            "include_mu_obs_uncertainty": True},
            "decision_rule": {"benefit_threshold": 1.0,
                              "recommend": {"p_benefit": 0.80, "upper": 1.0,
                                            "silent_rate_max": 0.50},
                              "consider": {"p_benefit": 0.60, "p_harm": 0.20,
                                           "silent_rate_max": 0.70},
                              "research": {"silent_rate_min": 0.40}},
            "ablation_modes": ["denom_only", "delta_only"],
        },
    })


def test_reproducibility():
    topic = _make_test_topic()
    r1 = run_topic(topic, 42, 2)
    r2 = run_topic(topic, 42, 2)

    for i in range(2):
        rr1 = r1["rep_results"][i]
        rr2 = r2["rep_results"][i]
        for nid in rr1["node_results"]:
            arb1 = rr1["node_results"][nid]["arbitration"]
            arb2 = rr2["node_results"][nid]["arbitration"]
            for key in ("mu", "ci_low", "ci_high", "disagreement"):
                v1, v2 = arb1.get(key), arb2.get(key)
                if v1 is not None and v2 is not None:
                    if not (math.isnan(v1) and math.isnan(v2)):
                        assert abs(v1 - v2) < 1e-10, \
                            f"Arb mismatch rep={i} node={nid} {key}"
    print("PASS: test_reproducibility (meta2)")


if __name__ == "__main__":
    test_reproducibility()
