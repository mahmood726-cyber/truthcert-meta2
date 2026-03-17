"""Test: arbitration intervals are NEVER narrower than delta engine intervals."""

import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sim.config_schema import TopicConfig
from sim.run_suite import run_topic


def _make_test_topic() -> TopicConfig:
    return TopicConfig(**{
        "topic_id": "T_cons",
        "label": "Conservative Test",
        "node_grid": {"phenotypes": ["P1", "P2"], "classes": ["C1"],
                      "endpoints": ["E1"]},
        "trial_count": {"n_trials_total": 30, "min_trials_per_node": 3,
                        "dispersion": 1.0},
        "sponsor": {"industry_rate": 0.6},
        "truth": {"mu_global": -0.10, "node_effect_structure": "smooth",
                  "mu_node_sd": 0.12, "tau_base": 0.10, "tau_sd": 0.03,
                  "discontinuity": {"enabled": False}},
        "baseline_risk": {"control_event_rate": {"E1": [0.10, 0.25]}},
        "sample_size": {"n_per_arm": [50, 300],
                        "size_distribution": "uniform"},
        "missingness": {
            "results_posting": {"base_rate": 0.55,
                                "coef": {"industry": 0.2, "signif_benefit": 0.5,
                                         "signif_harm": -0.3, "se": -0.2,
                                         "post2015": 0.2}},
            "publication": {"base_rate": 0.45,
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


def test_arbitration_conservative():
    """Arbitrated intervals must never be narrower than delta engine."""
    topic = _make_test_topic()
    result = run_topic(topic, 42, 5)

    violations = 0
    checks = 0

    for rep in result["rep_results"]:
        for nid, nr in rep["node_results"].items():
            engine = nr["engine_propagated"]
            arb = nr["arbitration"]

            d_lo = engine.get("mu_cri_low")
            d_hi = engine.get("mu_cri_high")
            a_lo = arb.get("ci_low")
            a_hi = arb.get("ci_high")

            if all(v is not None and math.isfinite(v)
                   for v in [d_lo, d_hi, a_lo, a_hi]):
                checks += 1
                d_width = d_hi - d_lo
                a_width = a_hi - a_lo

                # Check width (total width must not decrease)
                if a_width < d_width - 1e-10:
                    violations += 1

                # Check containment (neither tail should shrink)
                if a_lo > d_lo + 1e-10:
                    violations += 1
                if a_hi < d_hi - 1e-10:
                    violations += 1

    assert violations == 0, \
        f"{violations}/{checks} arbitrated intervals violated containment"
    print(f"PASS: test_arbitration_conservative ({checks} checks, 0 violations)")


if __name__ == "__main__":
    test_arbitration_conservative()
