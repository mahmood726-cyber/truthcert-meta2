# TruthCert Meta2: concrete submission fixes

This file converts the multi-persona review into repository-side actions that should be checked before external submission of the F1000 software paper for `truthcert-meta2-prototype`.

## Detectable Local State
- Documentation files detected: `README.md`, `f1000_artifacts/tutorial_walkthrough.md`.
- Environment lock or container files detected: `requirements.txt`.
- Package manifests detected: none detected.
- Example data files detected: `f1000_artifacts/example_dataset.csv`.
- Validation artifacts detected: `f1000_artifacts/validation_summary.md`, `tests/test_applied_example.py`, `tests/test_arbitration_conservative.py`, `tests/test_calibration_not_worse.py`, `tests/test_endpoint_reporting.py`, `tests/test_regret_improvement.py`, `tests/test_reproducibility.py`.
- Detected public repository root: `https://github.com/mahmood726-cyber/truthcert-meta2`.
- Detected public source snapshot: Fixed public commit snapshot available at `https://github.com/mahmood726-cyber/truthcert-meta2/tree/de3d284fd242760317f34e46af47d02bf58f2bd1`.
- Detected public archive record: No project-specific DOI or Zenodo record URL was detected locally; archive registration pending.

## High-Priority Fixes
- Check that the manuscript's named example paths exist in the public archive and can be run without repository archaeology.
- Confirm that the cited repository root (`https://github.com/mahmood726-cyber/truthcert-meta2`) resolves to the same fixed public source snapshot used for submission.
- Archive the tagged release and insert the Zenodo DOI or record URL once it has been minted; no project-specific archive DOI was detected locally.
- Reconfirm the quoted benchmark or validation sentence after the final rerun so the narrative text matches the shipped artifacts.

## Numeric Evidence Available To Quote
- `outputs/runs_v2/11bbba3dcee3/global_metrics.csv` reports 12 topics, 50 replications.
- `outputs/runs/11bbba3dcee3/global_metrics.csv` reports 12 topics, 50 replications.
- `paper/MANUSCRIPT_PLOS_ONE_TRUTHCERT.md` reports In the applied example (CD002042, 30-day mortality), 15/37 studies were CT.gov-registered with a 4.1% silent rate; the TruthCert framework produced appropriately wider intervals (risk ratio [RR] 1.02, 95% credible interval [CrI] 0.74-1.39) than classic RE (RR 1.01, 95%.

## Manuscript Files To Keep In Sync
- `F1000_Software_Tool_Article.md`
- `F1000_Reviewer_Rerun_Manifest.md`
- `F1000_MultiPersona_Review.md`
- `F1000_Submission_Checklist_RealReview.md` where present
- README/tutorial files and the public repository release metadata
