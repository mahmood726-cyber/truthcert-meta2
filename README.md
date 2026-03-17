# TruthCert Meta2 Prototype

## Installation
Use the dependency files in this directory (for example `requirements.txt`, `environment.yml`, `DESCRIPTION`, or equivalent project-specific files) to create a clean local environment before running analyses.
Document any package-version mismatch encountered during first run.

**Meta-Analysis 2.0: Governance overlay for denominator-first meta-analysis**

Extends Phase 1 (denominator-first engine) with a governance framework that ensures conservative, transparent, and auditable treatment-effect estimates.

## Concept

Traditional meta-analysis trusts whatever studies happen to be published. Phase 1 showed that using registry denominators + modeling silent-trial shifts (delta) reduces false reassurance. Meta2 adds a governance layer:

1. **Question Contract** — locks the estimand (population, intervention, comparator, endpoints, effect measure) before analysis
2. **Bias Decomposition** — quantifies silent-trial rate, endpoint missingness, publication missingness, and industry fraction per node
3. **3-Witness Panel** — assembles independent estimates from Classic FE (publications only), Delta Engine (denominator-corrected), and Selection Witness (IPW-adjusted)
4. **Conservative Arbitration** — compares witnesses, inflates uncertainty when they disagree, never shrinks intervals
5. **Calibration + Regret Scoring** — measures coverage (does the CI contain the oracle truth?) and decision regret (recommending harm or blocking benefit?)

## Quick Start

```bash
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Run individual tests
python tests/test_reproducibility.py
python tests/test_arbitration_conservative.py
python tests/test_regret_improvement.py
python tests/test_calibration_not_worse.py

# Full suite (12 topics, 50 replications)
python -m sim.run_suite --config configs/suite_12topics_meta2.json --out outputs/runs
```

## Architecture

```
sim/
  # Phase 1 core (inherited)
  seed.py               Deterministic seeding (PCG64, hash-chained)
  config_schema.py      Pydantic v2 config hierarchy
  generate_truth.py     Node-level truth parameters
  generate_trials.py    Dirichlet-multinomial trial allocation
  oracle.py             MNAR oracle shift mechanism
  selection.py          Two-stage selection (results posting + publication)
  observed_world.py     Build observed effects + denominator tables
  meta_fixed.py         Inverse-variance fixed-effect meta-analysis
  fit_delta.py          Bayesian delta posterior (coherence-likelihood grid)
  propagate_engine.py   Posterior sampling -> node-level estimates
  decision.py           Decision rules (Recommend/Consider/Research/DoNot)
  score.py              Phase 1 scoring metrics

  # Phase 2 governance (new)
  question_contract.py  Estimand lock with SHA-256 hash
  bias_decomposition.py 3-component bias profile per node
  selection_witness.py  IPW-adjusted pooled estimate
  witness_panel.py      3-witness assembly
  arbitration.py        Conservative interval arbitration
  calibration.py        Coverage metrics (arb vs delta vs classic)
  regret.py             Decision-regret scoring
  run_suite.py          Full Meta2 pipeline orchestrator

configs/
  suite_12topics_meta2.json   12 diverse clinical topics

tests/
  test_reproducibility.py           Deterministic output (same seed -> same result)
  test_arbitration_conservative.py  Arbitrated intervals never narrower than delta
  test_regret_improvement.py        Meta2 regret <= classic regret in high-silence
  test_calibration_not_worse.py     Arbitrated coverage >= delta coverage

outputs/
  runs/                 Suite output directory
```

## Key Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Coverage (arb) | >= 0.90 | Fraction of nodes where arbitrated CI contains oracle mu |
| Coverage (delta) | >= 0.85 | Same for delta engine CrI |
| Regret (arb) | < regret (classic) | Arbitrated decisions have lower regret than publication-only |
| Regret (delta) | < regret (classic) | Delta engine decisions also improve over classic |
| Conservative guarantee | 100% | Arbitrated intervals NEVER narrower than delta engine |

## Arbitration Logic

All thresholds are configurable via `engine.arbitration` in the topic config.

```
disagreement = std(mu_i) across witnesses (population SD)

if disagreement <= thresh_low (default 0.05):
    level = "low" -> use delta engine interval as-is
elif disagreement <= thresh_high (default 0.15):
    level = "mid" -> inflate interval width by 1.3x
else:
    level = "high" -> inflate by 2.0x + downgrade decision to Research
```

**Decision gates** (applied after arbitration):
1. **High disagreement gate (symmetric)**: under high witness disagreement, both benefit recommendations (Recommend, Consider-benefit) AND definitive blocks (DoNot, Consider-harm) are moved to "Research" — epistemic humility in both directions.
2. **Endpoint-missing gate**: if `endpoint_missing_rate > threshold` (default 0.40), benefit recommendations are capped at "Research".

## Regret Scoring

Decision regret compares three methods (Classic, Delta, Arbitrated) against oracle truth:
- **False positive**: recommending benefit when oracle says no benefit (weight: `w_fp`)
- **False negative**: blocking when oracle says benefit (weight: `w_fn` for DoNot/Consider-harm, `w_fn * 0.5` for Research)
- The reduced Research penalty (0.5x) reflects that deferring for more data is less costly than a definitive block.

The **Classic decision** uses a 4-tier symmetric structure (Recommend / Consider-benefit / Consider-harm / Research / DoNot) based on CI bounds and width, serving as a fair random-effects comparator.

## Outputs

Each suite run produces:
- `topic_metrics.csv` — per-topic coverage, regret, FR, and calibration
- `node_capsules.jsonl` — per-node audit capsules with contract hash, bias profile, witness estimates, arbitration result, and final decision
- `global_metrics.csv` — cross-topic averages
- `manifest.json` — run metadata (seed, config, framework version)

## Determinism

All randomness flows through `make_rng(seed_master, topic_id, rep)` using SHA-256 hash chaining into PCG64. Same config + same seed = identical output, verified by `test_reproducibility.py`.

## Requirements

- Python >= 3.10
- numpy >= 1.24.0
- pandas >= 2.0.0
- pydantic >= 2.0.0
- scipy >= 1.11.0
