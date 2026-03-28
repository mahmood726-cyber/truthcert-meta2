# TruthCert Meta2: reviewer rerun manifest

This manifest is the shortest reviewer-facing rerun path for the local software package. It lists the files that should be sufficient to recreate one worked example, inspect saved outputs, and verify that the manuscript claims remain bounded to what the repository actually demonstrates.

## Reviewer Entry Points
- Project directory: `C:\Models\truthcert-meta2-prototype`.
- Preferred documentation start points: `README.md`, `f1000_artifacts/tutorial_walkthrough.md`.
- Detected public repository root: `https://github.com/mahmood726-cyber/truthcert-meta2`.
- Detected public source snapshot: Fixed public commit snapshot available at `https://github.com/mahmood726-cyber/truthcert-meta2/tree/de3d284fd242760317f34e46af47d02bf58f2bd1`.
- Detected public archive record: No project-specific DOI or Zenodo record URL was detected locally; archive registration pending.
- Environment capture files: `requirements.txt`.
- Validation/test artifacts: `f1000_artifacts/validation_summary.md`, `tests/test_applied_example.py`, `tests/test_arbitration_conservative.py`, `tests/test_calibration_not_worse.py`, `tests/test_endpoint_reporting.py`, `tests/test_regret_improvement.py`, `tests/test_reproducibility.py`.

## Worked Example Inputs
- Manuscript-named example paths: `paper/MANUSCRIPT_PLOS_ONE_TRUTHCERT.md` as the main narrative source; `configs/suite_12topics_meta2.json` for the packaged simulation suite; `outputs/runs/` and `node_capsules.jsonl` for audit-ready outputs; f1000_artifacts/example_dataset.csv.
- Auto-detected sample/example files: `f1000_artifacts/example_dataset.csv`.

## Expected Outputs To Inspect
- Witness-specific and arbitrated intervals.
- Decision-regret and coverage summaries across simulated topics.
- Node-level audit capsules for governance review.

## Minimal Reviewer Rerun Sequence
- Start with the README/tutorial files listed below and keep the manuscript paths synchronized with the public archive.
- Create the local runtime from the detected environment capture files if available: `requirements.txt`.
- Run at least one named example path from the manuscript and confirm that the generated outputs match the saved validation materials.
- Quote one concrete numeric result from the local validation snippets below when preparing the final software paper.

## Local Numeric Evidence Available
- `outputs/runs_v2/11bbba3dcee3/global_metrics.csv` reports 12 topics, 50 replications.
- `outputs/runs/11bbba3dcee3/global_metrics.csv` reports 12 topics, 50 replications.
- `paper/MANUSCRIPT_PLOS_ONE_TRUTHCERT.md` reports In the applied example (CD002042, 30-day mortality), 15/37 studies were CT.gov-registered with a 4.1% silent rate; the TruthCert framework produced appropriately wider intervals (risk ratio [RR] 1.02, 95% credible interval [CrI] 0.74-1.39) than classic RE (RR 1.01, 95%.
