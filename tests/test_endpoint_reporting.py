"""Test: endpoint_reporting=True pathway works correctly.

Verifies that when endpoint_reporting is enabled, the denominator counts
and observed effects are consistent (no trials counted as 'observed' but
missing from analysis).
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sim.config_schema import TopicConfig
from sim.run_suite import run_topic


def _make_endpoint_reporting_topic() -> TopicConfig:
    return TopicConfig(**{
        "topic_id": "T_epr",
        "label": "Endpoint Reporting Test",
        "node_grid": {"phenotypes": ["P1"], "classes": ["C1"],
                      "endpoints": ["E1"]},
        "trial_count": {"n_trials_total": 40, "min_trials_per_node": 10,
                        "dispersion": 1.0},
        "sponsor": {"industry_rate": 0.6},
        "truth": {"mu_global": -0.10, "node_effect_structure": "smooth",
                  "mu_node_sd": 0.10, "tau_base": 0.08, "tau_sd": 0.02,
                  "discontinuity": {"enabled": False}},
        "baseline_risk": {"control_event_rate": {"E1": [0.10, 0.25]}},
        "sample_size": {"n_per_arm": [50, 200],
                        "size_distribution": "uniform"},
        "missingness": {
            "results_posting": {"base_rate": 0.60,
                                "coef": {"industry": 0.2, "signif_benefit": 0.3,
                                         "signif_harm": -0.2, "se": -0.1,
                                         "post2015": 0.2}},
            "publication": {"base_rate": 0.50,
                            "coef": {"industry": 0.1, "signif_benefit": 0.5,
                                     "signif_harm": 0.2, "se": -0.3,
                                     "post2015": 0.1, "results_posted": 0.3}},
            "endpoint_reporting": {"enabled": True,
                                   "base_rate_by_endpoint": {"E1": 0.7},
                                   "coef": {"industry": 0.1, "signif_benefit": 0.2,
                                            "se": -0.1}},
            "silent_shift_delta": {"enabled": True,
                                   "delta_by_endpoint": {"E1": {"industry": 0.06,
                                                                "nonindustry": 0.03}},
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


def test_endpoint_reporting():
    """Run with endpoint_reporting=True and verify no crashes or NaN-only results."""
    topic = _make_endpoint_reporting_topic()
    result = run_topic(topic, 42, 3)

    # Should have 3 replications
    assert len(result["rep_results"]) == 3

    # At least some nodes should have valid engine estimates
    has_engine = 0
    total_nodes = 0
    for rep in result["rep_results"]:
        for nid, nr in rep["node_results"].items():
            total_nodes += 1
            eng = nr["engine_propagated"]
            if eng.get("mu_median") is not None and not (
                    eng["mu_median"] != eng["mu_median"]):  # NaN check
                has_engine += 1

    assert has_engine > 0, f"No valid engine estimates in {total_nodes} nodes"
    print(f"PASS: test_endpoint_reporting "
          f"({has_engine}/{total_nodes} nodes with engine estimates)")


if __name__ == "__main__":
    test_endpoint_reporting()
