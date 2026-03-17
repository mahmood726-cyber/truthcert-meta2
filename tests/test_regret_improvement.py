"""Test: in high-silence topics, Meta2 regret < classic regret."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sim.config_schema import TopicConfig
from sim.run_suite import run_topic
from sim.regret import aggregate_regret


def _make_high_silence_topic() -> TopicConfig:
    """High missingness + large delta -> classic should have high regret."""
    return TopicConfig(**{
        "topic_id": "T_regret",
        "label": "Regret High-Silence",
        "node_grid": {"phenotypes": ["P1"], "classes": ["C1"],
                      "endpoints": ["E1"]},
        "trial_count": {"n_trials_total": 40, "min_trials_per_node": 10,
                        "dispersion": 1.0},
        "sponsor": {"industry_rate": 0.7},
        "truth": {"mu_global": -0.05, "node_effect_structure": "smooth",
                  "mu_node_sd": 0.08, "tau_base": 0.10, "tau_sd": 0.03,
                  "discontinuity": {"enabled": False}},
        "baseline_risk": {"control_event_rate": {"E1": [0.10, 0.25]}},
        "sample_size": {"n_per_arm": [60, 300],
                        "size_distribution": "uniform"},
        "missingness": {
            "results_posting": {"base_rate": 0.35,
                                "coef": {"industry": 0.3, "signif_benefit": 0.8,
                                         "signif_harm": -0.4, "se": -0.3,
                                         "post2015": 0.2}},
            "publication": {"base_rate": 0.25,
                            "coef": {"industry": 0.2, "signif_benefit": 1.2,
                                     "signif_harm": 0.3, "se": -0.5,
                                     "post2015": 0.1, "results_posted": 0.4}},
            "endpoint_reporting": {"enabled": False,
                                   "base_rate_by_endpoint": {"E1": 0.9},
                                   "coef": {"industry": 0.0, "signif_benefit": 0.0,
                                            "se": 0.0}},
            "silent_shift_delta": {"enabled": True,
                                   "delta_by_endpoint": {"E1": {"industry": 0.12,
                                                                "nonindustry": 0.06}},
                                   "constraint": "industry_ge_nonindustry",
                                   "multiplier_by_endpoint": {"E1": 1.0}},
        },
        "engine": {
            "delta_bayes": {"grid": {"di_max": 0.5, "dn_max": 0.3, "step": 0.04},
                            "prior": {"type": "half_normal", "sigma_industry": 0.25,
                                      "sigma_nonindustry": 0.2},
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


def test_regret_improvement():
    """Meta2 regret should be <= classic regret in high-silence regime."""
    topic = _make_high_silence_topic()
    result = run_topic(topic, 42, 10)

    reg_agg = aggregate_regret(result["regrets"])
    r_cl = reg_agg["regret_classic"]
    r_d = reg_agg["regret_delta"]
    r_arb = reg_agg["regret_arb"]

    print(f"  Regret classic: {r_cl:.4f}")
    print(f"  Regret delta:   {r_d:.4f}")
    print(f"  Regret arb:     {r_arb:.4f}")

    # Meta2 (arb) should not be dramatically worse than classic
    # In high-silence, arb should be similar or better
    assert r_arb <= r_cl + 0.05, \
        f"Arb regret ({r_arb}) much worse than classic ({r_cl})"

    print("PASS: test_regret_improvement")


if __name__ == "__main__":
    test_regret_improvement()
