# TruthCert Meta2: multi-persona peer review

This memo applies the recurring concerns in the supplied peer-review document to the current F1000 draft for this project (`truthcert-meta2-prototype`). It distinguishes changes already made in the draft from repository-side items that still need to hold in the released repository and manuscript bundle.

## Detected Local Evidence
- Detected documentation files: `README.md`, `f1000_artifacts/tutorial_walkthrough.md`.
- Detected environment capture or packaging files: `requirements.txt`.
- Detected validation/test artifacts: `f1000_artifacts/validation_summary.md`, `tests/test_applied_example.py`, `tests/test_arbitration_conservative.py`, `tests/test_calibration_not_worse.py`, `tests/test_endpoint_reporting.py`, `tests/test_regret_improvement.py`, `tests/test_reproducibility.py`.
- Detected browser deliverables: no HTML file detected.
- Detected public repository root: `https://github.com/mahmood726-cyber/truthcert-meta2`.
- Detected public source snapshot: Fixed public commit snapshot available at `https://github.com/mahmood726-cyber/truthcert-meta2/tree/de3d284fd242760317f34e46af47d02bf58f2bd1`.
- Detected public archive record: No project-specific DOI or Zenodo record URL was detected locally; archive registration pending.

## Reviewer Rerun Companion
- `F1000_Reviewer_Rerun_Manifest.md` consolidates the shortest reviewer-facing rerun path, named example files, environment capture, and validation checkpoints.

## Detected Quantitative Evidence
- `outputs/runs_v2/11bbba3dcee3/global_metrics.csv` reports 12 topics, 50 replications.
- `outputs/runs/11bbba3dcee3/global_metrics.csv` reports 12 topics, 50 replications.
- `paper/MANUSCRIPT_PLOS_ONE_TRUTHCERT.md` reports In the applied example (CD002042, 30-day mortality), 15/37 studies were CT.gov-registered with a 4.1% silent rate; the TruthCert framework produced appropriately wider intervals (risk ratio [RR] 1.02, 95% credible interval [CrI] 0.74-1.39) than classic RE (RR 1.01, 95%.

## Current Draft Strengths
- States the project rationale and niche explicitly: Bias correction alone is not enough when multiple analytic perspectives disagree. TruthCert Meta2 extends denominator-first meta-analysis with explicit governance so that disagreement itself becomes part of the output rather than hidden in analyst judgment.
- Names concrete worked-example paths: `paper/MANUSCRIPT_PLOS_ONE_TRUTHCERT.md` as the main narrative source; `configs/suite_12topics_meta2.json` for the packaged simulation suite; `outputs/runs/` and `node_capsules.jsonl` for audit-ready outputs.
- Points reviewers to local validation materials: `tests/test_arbitration_conservative.py`, `test_regret_improvement.py`, and `test_calibration_not_worse.py`; Deterministic seeding and reproducibility checks; Per-topic metrics and audit-capsule outputs documenting disagreement handling.
- Moderates conclusions and lists explicit limitations for TruthCert Meta2.

## Remaining High-Priority Fixes
- Keep one minimal worked example public and ensure the manuscript paths match the released files.
- Ensure README/tutorial text, software availability metadata, and public runtime instructions stay synchronized with the manuscript.
- Confirm that the cited repository root resolves to the same fixed public source snapshot used for the submission package.
- Mint and cite a Zenodo DOI or record URL for the tagged release; none was detected locally.
- Reconfirm the quoted benchmark or validation sentence after the final rerun so the narrative text stays synchronized with the shipped artifacts.

## Persona Reviews

### Reproducibility Auditor
- Review question: Looks for a frozen computational environment, a fixed example input, and an end-to-end rerun path with saved outputs.
- What the revised draft now provides: The revised draft names concrete rerun assets such as `paper/MANUSCRIPT_PLOS_ONE_TRUTHCERT.md` as the main narrative source; `configs/suite_12topics_meta2.json` for the packaged simulation suite and ties them to validation files such as `tests/test_arbitration_conservative.py`, `test_regret_improvement.py`, and `test_calibration_not_worse.py`; Deterministic seeding and reproducibility checks.
- What still needs confirmation before submission: Before submission, freeze the public runtime with `requirements.txt` and keep at least one minimal example input accessible in the external archive.

### Validation and Benchmarking Statistician
- Review question: Checks whether the paper shows evidence that outputs are accurate, reproducible, and compared against known references or stress tests.
- What the revised draft now provides: The manuscript now cites concrete validation evidence including `tests/test_arbitration_conservative.py`, `test_regret_improvement.py`, and `test_calibration_not_worse.py`; Deterministic seeding and reproducibility checks; Per-topic metrics and audit-capsule outputs documenting disagreement handling and frames conclusions as being supported by those materials rather than by interface availability alone.
- What still needs confirmation before submission: Concrete numeric evidence detected locally is now available for quotation: `outputs/runs_v2/11bbba3dcee3/global_metrics.csv` reports 12 topics, 50 replications; `outputs/runs/11bbba3dcee3/global_metrics.csv` reports 12 topics, 50 replications.

### Methods-Rigor Reviewer
- Review question: Examines modeling assumptions, scope conditions, and whether method-specific caveats are stated instead of implied.
- What the revised draft now provides: The architecture and discussion sections now state the method scope explicitly and keep caveats visible through limitations such as Current validation is still dominated by simulation evidence; The selection witness is a pragmatic perturbation rather than a fully identifiable selection model.
- What still needs confirmation before submission: Retain method-specific caveats in the final Results and Discussion and avoid collapsing exploratory thresholds or heuristics into universal recommendations.

### Comparator and Positioning Reviewer
- Review question: Asks what gap the tool fills relative to existing software and whether the manuscript avoids unsupported superiority claims.
- What the revised draft now provides: The introduction now positions the software against an explicit comparator class: The key comparator is a fair publication-only random-effects workflow, not a straw-man baseline. This framing is already built into the local paper and should be preserved in the F1000 version.
- What still needs confirmation before submission: Keep the comparator discussion citation-backed in the final submission and avoid phrasing that implies blanket superiority over better-established tools.

### Documentation and Usability Reviewer
- Review question: Looks for a README, tutorial, worked example, input-schema clarity, and short interpretation guidance for outputs.
- What the revised draft now provides: The revised draft points readers to concrete walkthrough materials such as `paper/MANUSCRIPT_PLOS_ONE_TRUTHCERT.md` as the main narrative source; `configs/suite_12topics_meta2.json` for the packaged simulation suite; `outputs/runs/` and `node_capsules.jsonl` for audit-ready outputs and spells out expected outputs in the Methods section.
- What still needs confirmation before submission: Make sure the public archive exposes a readable README/tutorial bundle: currently detected files include `README.md`, `f1000_artifacts/tutorial_walkthrough.md`.

### Software Engineering Hygiene Reviewer
- Review question: Checks for evidence of testing, deployment hygiene, browser/runtime verification, secret handling, and removal of obvious development leftovers.
- What the revised draft now provides: The draft now foregrounds regression and validation evidence via `f1000_artifacts/validation_summary.md`, `tests/test_applied_example.py`, `tests/test_arbitration_conservative.py`, `tests/test_calibration_not_worse.py`, `tests/test_endpoint_reporting.py`, `tests/test_regret_improvement.py`, `tests/test_reproducibility.py`, and browser-facing projects are described as self-validating where applicable.
- What still needs confirmation before submission: Before submission, remove any dead links, exposed secrets, or development-stage text from the public repo and ensure the runtime path described in the manuscript matches the shipped code.

### Claims-and-Limitations Editor
- Review question: Verifies that conclusions are bounded to what the repository actually demonstrates and that limitations are explicit.
- What the revised draft now provides: The abstract and discussion now moderate claims and pair them with explicit limitations, including Current validation is still dominated by simulation evidence; The selection witness is a pragmatic perturbation rather than a fully identifiable selection model; Arbitrated intervals may overcover and require further calibration.
- What still needs confirmation before submission: Keep the conclusion tied to documented functions and artifacts only; avoid adding impact claims that are not directly backed by validation, benchmarking, or user-study evidence.

### F1000 and Editorial Compliance Reviewer
- Review question: Checks for manuscript completeness, software/data availability clarity, references, and reviewer-facing support files.
- What the revised draft now provides: The revised draft is more complete structurally and now points reviewers to software availability, data availability, and reviewer-facing support files.
- What still needs confirmation before submission: Confirm repository/archive metadata, figure/export requirements, and supporting-file synchronization before release.
