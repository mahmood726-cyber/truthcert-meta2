"""Applied example: TruthCert on Cochrane CD002042 (Transfusion Thresholds).

Uses real Cochrane review data (30-day mortality, 44 studies) combined with
ClinicalTrials.gov registry denominators to demonstrate the denominator-first
delta engine on a real meta-analysis.

Data source: Carson et al. (2025). Transfusion thresholds and other strategies
for guiding red blood cell transfusion. Cochrane Database Syst Rev.
DOI: 10.1002/14651858.CD002042.pub6

Usage:
    python applied_example_cd002042.py
"""

import csv
import math
import sys
import io
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from sim.meta_fixed import fixed_effect, random_effects_dl, i_squared
from sim.propagate_engine import _estimate_tau_sq

Z_ALPHA_05 = norm.ppf(0.975)

# ── Registry data: NCT enrollment counts ────────────────────────────────
# Mapping: study label -> (NCT_ID, enrolled_on_registry, is_industry)
# Source: ClinicalTrials.gov search February 2026
REGISTRY = {
    "Carson 2011 (FOCUS)":          ("NCT00071032", 2016, False),
    "Carson 2023a (MINT)":          ("NCT02981407", 3506, False),
    "Carson 2013 (MINT pilot)":     ("NCT01167582", 110,  False),
    "Mazer 2017 (TRICS III)":       ("NCT02042898", 5028, False),
    "Holst 2014 (TRISS)":          ("NCT01485315", 1005, False),
    "Hajjar 2010 (TRACS)":         ("NCT01021631", 500,  False),
    "Ducrocq 2021 (REALITY)":      ("NCT02648113", 668,  False),
    "Jairath 2015 (TRIGGER)":      ("NCT02105532", 936,  False),
    "Taccone 2024 (TRAIN)":        ("NCT02968654", 850,  False),
    "Gobatto 2019 (TRAHT)":        ("NCT02203292", 44,   False),
    "Bergamin 2017 (TRICOP)":      ("NCT01648946", 300,  True),
    "Gregersen 2015 (TRIFE)":      ("NCT01102010", 284,  False),
    "Gillies 2020 (RESULT-NOF)":   ("NCT03407573", 200,  False),
    "Walsh 2013 (RELIEVE)":        ("NCT00944112", 100,  False),
    "Prick 2014 (WOMB)":           ("NCT00335023", 500,  False),
    "Buckstein 2024a (RBC-ENHANCE)": ("NCT02099669", 30, False),
    "Mullis 2023 (ORACL)":         ("NCT02972593", 161,  False),
    "Palmieri 2017 (TRIBE)":       ("NCT01079247", 347,  False),
    # Trials not on CT.gov (ISRCTN/national registries) — mark as not registered
    # TITRe2 (ISRCTN70923932), TRICC (pre-registration era),
    # TRIPICU (ISRCTN07448790), TRACT (ISRCTN84086586)
}


def log_rr_and_se(e_t, n_t, e_c, n_c, cc=0.5):
    """Compute log risk ratio and SE with continuity correction."""
    if n_t <= 0 or n_c <= 0:
        return np.nan, np.nan
    # Apply cc if any zero cell
    if e_t == 0 or e_c == 0 or e_t == n_t or e_c == n_c:
        e_t_a = e_t + cc
        n_t_a = n_t + 2 * cc
        e_c_a = e_c + cc
        n_c_a = n_c + 2 * cc
    else:
        e_t_a, n_t_a = float(e_t), float(n_t)
        e_c_a, n_c_a = float(e_c), float(n_c)

    p_t = e_t_a / n_t_a
    p_c = e_c_a / n_c_a
    if p_t <= 0 or p_c <= 0:
        return np.nan, np.nan
    logRR = math.log(p_t / p_c)
    se = math.sqrt(1.0 / e_t_a - 1.0 / n_t_a + 1.0 / e_c_a - 1.0 / n_c_a)
    return logRR, se


def main():
    data_path = Path(__file__).parent / "data" / "cd002042_mortality.csv"
    if not data_path.exists():
        print(f"ERROR: {data_path} not found. Run R extraction first.")
        return

    # ── Load and prepare data ───────────────────────────────────────────
    rows = []
    with open(data_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip subgroup-only duplicates (keep main analysis rows only)
            if row["Subgroup"].strip():
                continue
            e_t = int(row["Experimental.cases"])
            n_t = int(row["Experimental.N"])
            e_c = int(row["Control.cases"])
            n_c = int(row["Control.N"])
            # Skip double-zero studies
            if e_t == 0 and e_c == 0:
                continue
            logRR, se = log_rr_and_se(e_t, n_t, e_c, n_c)
            if not (np.isfinite(logRR) and np.isfinite(se) and se > 0):
                continue
            reg = REGISTRY.get(row["Study"].strip())
            rows.append({
                "study": row["Study"].strip(),
                "year": row["Study.year"].strip() if row["Study.year"].strip() != "NA" else "",
                "e_t": e_t, "n_t": n_t, "e_c": e_c, "n_c": n_c,
                "logRR": logRR, "se": se,
                "registered": reg is not None,
                "nct_id": reg[0] if reg else "",
                "enrolled_registry": reg[1] if reg else 0,
                "is_industry": reg[2] if reg else False,
            })

    df = pd.DataFrame(rows)
    k_total = len(df)
    k_registered = df["registered"].sum()
    print("=" * 70)
    print("TRUTHCERT APPLIED EXAMPLE: CD002042 (Transfusion Thresholds)")
    print("  Outcome: 30-day mortality (restrictive vs liberal)")
    print(f"  Studies included: {k_total} (excl double-zero)")
    print(f"  CT.gov registered: {k_registered}")
    print(f"  Not on CT.gov: {k_total - k_registered}")
    print("=" * 70)

    # ── Step 1: Classic RE meta-analysis (published data only) ──────────
    logRR_arr = df["logRR"].values
    se_arr = df["se"].values
    re_all = random_effects_dl(logRR_arr, se_arr)
    fe_all = fixed_effect(logRR_arr, se_arr)
    I2 = i_squared(logRR_arr, se_arr)

    print("\n--- Step 1: Classic Meta-Analysis (all studies) ---")
    print(f"  Fixed-effect:   RR = {math.exp(fe_all['mu']):.3f} "
          f"(95% CI: {math.exp(fe_all['ci_low']):.3f}-{math.exp(fe_all['ci_high']):.3f})")
    print(f"  Random-effects: RR = {math.exp(re_all['mu']):.3f} "
          f"(95% CI: {math.exp(re_all['ci_low']):.3f}-{math.exp(re_all['ci_high']):.3f})")
    print(f"  I-squared: {I2:.1f}%")
    print(f"  Tau-squared: {re_all['tau2']:.4f}")
    print(f"  k = {re_all['k']}")

    # ── Step 2: Denominator analysis ────────────────────────────────────
    # For registered trials: compare published N vs registry enrollment
    print("\n--- Step 2: Denominator Analysis ---")
    n_published_total = int(df["n_t"].sum() + df["n_c"].sum())
    n_registry_total = int(df["enrolled_registry"].sum())

    reg_df = df[df["registered"]]
    n_pub_registered = int(reg_df["n_t"].sum() + reg_df["n_c"].sum())
    n_reg_enrolled = int(reg_df["enrolled_registry"].sum())

    print(f"  Registered trials: {len(reg_df)}")
    print(f"    Published participants: {n_pub_registered:,}")
    print(f"    Registry enrollment:    {n_reg_enrolled:,}")
    denominator_ratio = n_pub_registered / n_reg_enrolled if n_reg_enrolled > 0 else 1.0
    print(f"    Pub/Registry ratio:     {denominator_ratio:.3f}")
    if denominator_ratio < 1.0:
        gap = n_reg_enrolled - n_pub_registered
        print(f"    --> {gap:,} participants registered but not in published analysis")
        silent_rate = 1.0 - denominator_ratio
        print(f"    --> Silent rate: {silent_rate:.1%}")
    else:
        silent_rate = 0.0
        print(f"    --> No silent participants detected")

    # Per-trial comparison
    print("\n  Per-trial denominator comparison (registered only):")
    print(f"  {'Study':<35} {'Pub N':>8} {'Reg N':>8} {'Ratio':>8} {'Gap':>6}")
    print("  " + "-" * 65)
    for _, r in reg_df.iterrows():
        pub_n = r["n_t"] + r["n_c"]
        reg_n = r["enrolled_registry"]
        ratio = pub_n / reg_n if reg_n > 0 else 0
        gap = reg_n - pub_n
        flag = " *" if gap > 10 else ""
        print(f"  {r['study']:<35} {pub_n:>8} {reg_n:>8} {ratio:>8.2f} {gap:>6}{flag}")

    # ── Step 3: Delta estimation ────────────────────────────────────────
    # Simplified delta: the "missing" participants' effect as a shift
    # Using denominator-first principle:
    #   shift = silent_rate * delta
    #   where delta is the hypothetical mean effect among silent participants
    print("\n--- Step 3: Sensitivity Analysis (Denominator-First) ---")

    # Grid search over plausible delta values
    delta_grid = np.linspace(-0.5, 0.5, 101)  # log-RR scale
    mu_obs = re_all["mu"]
    se_obs = re_all["se"]
    tau_sq = re_all["tau2"]

    print(f"\n  Observed RE estimate: logRR = {mu_obs:.4f} (RR = {math.exp(mu_obs):.3f})")
    print(f"  Silent rate: {silent_rate:.3f}")
    print(f"\n  Sensitivity: adjusted RR across delta values")
    print(f"  {'delta':>8} {'shift':>8} {'adj logRR':>10} {'adj RR':>8} {'CI low':>8} {'CI high':>8} {'Verdict':>12}")
    print("  " + "-" * 72)

    for delta in [-0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3]:
        shift = silent_rate * delta
        adj_mu = mu_obs + shift
        # Prediction variance includes tau2 + SE2 + shift uncertainty
        pred_var = se_obs ** 2 + tau_sq + (silent_rate * 0.15) ** 2
        adj_ci_lo = adj_mu - Z_ALPHA_05 * math.sqrt(pred_var)
        adj_ci_hi = adj_mu + Z_ALPHA_05 * math.sqrt(pred_var)
        rr = math.exp(adj_mu)
        rr_lo = math.exp(adj_ci_lo)
        rr_hi = math.exp(adj_ci_hi)

        if adj_ci_hi < 0:
            verdict = "Recommend"
        elif adj_ci_lo > 0:
            verdict = "DoNot"
        elif adj_mu < 0 and (adj_ci_hi - adj_ci_lo) < 0.6:
            verdict = "Consider"
        else:
            verdict = "Research"

        print(f"  {delta:>8.2f} {shift:>8.3f} {adj_mu:>10.4f} "
              f"{rr:>8.3f} {rr_lo:>8.3f} {rr_hi:>8.3f} {verdict:>12}")

    # ── Step 4: Posterior propagation (Monte Carlo) ─────────────────────
    print("\n--- Step 4: Posterior Propagation (10,000 samples) ---")
    rng = np.random.default_rng(42)
    n_samples = 10_000

    # Prior on delta: N(0, 0.15^2) - mildly informative toward null
    delta_samples = rng.normal(0, 0.15, size=n_samples)

    # Observation uncertainty (prediction-type: SE^2 + tau^2 + sigma_floor^2)
    sigma_floor = 0.05
    mu_obs_samples = rng.normal(mu_obs,
                                math.sqrt(se_obs ** 2 + tau_sq + sigma_floor ** 2),
                                size=n_samples)

    # Shift = silent_rate * delta
    shifts = silent_rate * delta_samples

    # Compensated effect
    mu_comp = mu_obs_samples + shifts
    rr_comp = np.exp(mu_comp)

    p_benefit = float(np.mean(mu_comp < 0))
    p_harm = float(np.mean(mu_comp > 0))
    p_near_null = float(np.mean(np.abs(mu_comp) <= 0.02))

    mu_median = float(np.median(mu_comp))
    mu_cri_lo = float(np.percentile(mu_comp, 2.5))
    mu_cri_hi = float(np.percentile(mu_comp, 97.5))

    print(f"  Posterior median logRR: {mu_median:.4f} (RR = {math.exp(mu_median):.3f})")
    print(f"  95% CrI: ({mu_cri_lo:.4f}, {mu_cri_hi:.4f})")
    print(f"         = RR ({math.exp(mu_cri_lo):.3f}, {math.exp(mu_cri_hi):.3f})")
    print(f"  P(benefit):   {p_benefit:.3f}")
    print(f"  P(harm):      {p_harm:.3f}")
    print(f"  P(near null): {p_near_null:.3f}")

    # Decision (thresholds aligned with main engine decision.py)
    if p_benefit >= 0.80 and math.exp(mu_cri_hi) < 1.0 and silent_rate <= 0.50:
        decision = "Recommend"
    elif (p_benefit >= 0.60 or p_harm >= 0.20) and silent_rate <= 0.70:
        # Direction logic matches decision.py: benefit if p_benefit >= threshold
        direction = "benefit" if p_benefit >= 0.60 else "harm"
        decision = f"Consider-{direction}"
    elif silent_rate >= 0.40:
        decision = "Research"
    else:
        decision = "DoNot"

    print(f"\n  TruthCert Decision: {decision}")
    print(f"  (silent_rate={silent_rate:.3f}, p_benefit={p_benefit:.3f})")

    # ── Step 5: Comparison with classic ─────────────────────────────────
    print("\n--- Step 5: Classic vs TruthCert Comparison ---")
    print(f"  {'Method':<25} {'RR':>8} {'CI/CrI low':>12} {'CI/CrI high':>12} {'Width':>8}")
    print("  " + "-" * 65)

    fe_width = fe_all["ci_high"] - fe_all["ci_low"]
    re_width = re_all["ci_high"] - re_all["ci_low"]
    tc_width = mu_cri_hi - mu_cri_lo

    print(f"  {'Fixed-effect':<25} {math.exp(fe_all['mu']):>8.3f} "
          f"{math.exp(fe_all['ci_low']):>12.3f} {math.exp(fe_all['ci_high']):>12.3f} "
          f"{fe_width:>8.3f}")
    print(f"  {'Random-effects (DL)':<25} {math.exp(re_all['mu']):>8.3f} "
          f"{math.exp(re_all['ci_low']):>12.3f} {math.exp(re_all['ci_high']):>12.3f} "
          f"{re_width:>8.3f}")
    print(f"  {'TruthCert (posterior)':<25} {math.exp(mu_median):>8.3f} "
          f"{math.exp(mu_cri_lo):>12.3f} {math.exp(mu_cri_hi):>12.3f} "
          f"{tc_width:>8.3f}")

    print(f"\n  TruthCert interval is {'wider' if tc_width > re_width else 'narrower'} "
          f"than RE by {abs(tc_width - re_width):.3f} "
          f"({abs(tc_width - re_width) / re_width * 100:.1f}%)")
    print(f"  This reflects the additional uncertainty from {silent_rate:.1%} "
          f"silent participants")

    # ── Summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Cochrane Review: CD002042 (Carson et al. 2025)")
    print(f"  Outcome: 30-day mortality, restrictive vs liberal transfusion")
    print(f"  Studies: {k_total} (after excluding double-zero)")
    print(f"  CT.gov registered: {k_registered} ({k_registered/k_total*100:.0f}%)")
    print(f"  Published/registered ratio: {denominator_ratio:.3f}")
    print(f"  Silent rate: {silent_rate:.1%}")
    print(f"  Classic RE: RR = {math.exp(re_all['mu']):.3f} "
          f"({math.exp(re_all['ci_low']):.3f}-{math.exp(re_all['ci_high']):.3f})")
    print(f"  TruthCert: RR = {math.exp(mu_median):.3f} "
          f"({math.exp(mu_cri_lo):.3f}-{math.exp(mu_cri_hi):.3f})")
    print(f"  TruthCert decision: {decision}")
    print(f"  P(benefit): {p_benefit:.3f}")
    print("=" * 70)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    main()
