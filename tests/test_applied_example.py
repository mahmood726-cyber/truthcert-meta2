"""Test: applied example CD002042 produces expected outputs."""

import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_applied_example():
    """Run applied example and verify key outputs match manuscript."""
    from pathlib import Path
    import csv
    import numpy as np
    from sim.meta_fixed import random_effects_dl, i_squared

    data_path = Path(__file__).parent.parent / "data" / "cd002042_mortality.csv"
    assert data_path.exists(), f"Data file not found: {data_path}"

    # Load data (same logic as applied_example_cd002042.py)
    from applied_example_cd002042 import log_rr_and_se, REGISTRY

    rows = []
    with open(data_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Subgroup"].strip():
                continue
            e_t = int(row["Experimental.cases"])
            n_t = int(row["Experimental.N"])
            e_c = int(row["Control.cases"])
            n_c = int(row["Control.N"])
            if e_t == 0 and e_c == 0:
                continue
            logRR, se = log_rr_and_se(e_t, n_t, e_c, n_c)
            if not (np.isfinite(logRR) and np.isfinite(se) and se > 0):
                continue
            rows.append({"logRR": logRR, "se": se,
                         "study": row["Study"].strip(),
                         "registered": row["Study"].strip() in REGISTRY})

    # Check study count
    assert len(rows) == 37, f"Expected 37 studies, got {len(rows)}"

    # Check registered count
    n_reg = sum(1 for r in rows if r["registered"])
    assert n_reg == 15, f"Expected 15 registered, got {n_reg}"

    # Check RE meta-analysis
    logRR_arr = np.array([r["logRR"] for r in rows])
    se_arr = np.array([r["se"] for r in rows])
    re = random_effects_dl(logRR_arr, se_arr)
    I2 = i_squared(logRR_arr, se_arr)

    rr_re = math.exp(re["mu"])
    assert abs(rr_re - 1.013) < 0.002, f"RE RR {rr_re:.4f} != 1.013"
    assert abs(I2 - 22.0) < 2.0, f"I2 {I2:.1f}% != 22%"

    print(f"  Studies: {len(rows)}, Registered: {n_reg}")
    print(f"  RE RR: {rr_re:.3f}, I2: {I2:.1f}%")
    print("PASS: test_applied_example")


if __name__ == "__main__":
    test_applied_example()
