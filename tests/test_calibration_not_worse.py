"""Test: Meta2 arbitrated coverage >= delta engine coverage (minus tolerance)."""

import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sim.config_schema import TopicConfig
from sim.run_suite import run_topic
from sim.calibration import aggregate_calibration


def _make_test_topic() -> TopicConfig:
    """Moderate missingness topic for calibration comparison."""
    return TopicConfig(**{
        "topic_id": "T_cal",
        "label": "Calibration Test",
        "node_grid": {"phenotypes": ["P1", "P2"], "classes": ["C1"],
                      "endpoints": ["E1"]},
        "trial_count": {"n_trials_total": 30, "min_trials_per_node": 5,
                        "dispersion": 1.0},
        "sponsor": {"industry_rate": 0.6},
        "truth": {"mu_global": -0.10, "node_effect_structure": "smooth",
                  "mu_node_sd": 0.10, "tau_base": 0.10, "tau_sd": 0.03,
                  "discontinuity": {"enabled": False}},
        "baseline_risk": {"control_event_rate": {"E1": [0.10, 0.25]}},
        "sample_size": {"n_per_arm": [50, 250],
                        "size_distribution": "uniform"},
        "missingness": {
            "results_posting": {"base_rate": 0.50,
                                "coef": {"industry": 0.2, "signif_benefit": 0.5,
                                         "signif_harm": -0.3, "se": -0.2,
                                         "post2015": 0.2}},
            "publication": {"base_rate": 0.40,
                            "coef": {"industry": 0.15, "signif_benefit": 0.7,
                                     "signif_harm": 0.2, "se": -0.3,
                                     "post2015": 0.1, "results_posted": 0.3}},
            "endpoint_reporting": {"enabled": False,
                                   "base_rate_by_endpoint": {"E1": 0.9},
                                   "coef": {"industry": 0.0, "signif_benefit": 0.0,
                                            "se": 0.0}},
            "silent_shift_delta": {"enabled": True,
                                   "delta_by_endpoint": {"E1": {"industry": 0.06,
                                                                "nonindustry": 0.03}},
                                   "constraint": "industry_ge_nonindustry",
                                   "multiplier_by_endpoint": {"E1": 1.0}},
        },
        "engine": {
            "delta_bayes": {"grid": {"di_max": 0.3, "dn_max": 0.2, "step": 0.04},
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


def test_calibration_not_worse():
    """Arbitrated coverage should not be worse than delta engine coverage."""
    topic = _make_test_topic()
    result = run_topic(topic, 42, 10)

    cal_agg = aggregate_calibration(result["calibrations"])
    cov_arb = cal_agg.get("coverage_arb", 0.0)
    cov_delta = cal_agg.get("coverage_delta", 0.0)
    cov_classic = cal_agg.get("coverage_classic", 0.0)

    print(f"  Coverage arb:     {cov_arb:.4f}")
    print(f"  Coverage delta:   {cov_delta:.4f}")
    print(f"  Coverage classic: {cov_classic:.4f}")

    # Arbitrated intervals are wider, so coverage should be >= delta - tolerance
    assert cov_arb >= cov_delta - 0.02, \
        f"Arb coverage ({cov_arb:.4f}) worse than delta ({cov_delta:.4f})"

    # Absolute coverage: all methods should achieve >= 95% (nominal level)
    assert cov_arb >= 0.95, \
        f"Arb coverage ({cov_arb:.4f}) below 95% nominal level"
    assert cov_classic >= 0.90, \
        f"Classic coverage ({cov_classic:.4f}) below 90% floor"

    print("PASS: test_calibration_not_worse")


if __name__ == "__main__":
    test_calibration_not_worse()
