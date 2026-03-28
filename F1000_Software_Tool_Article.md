# TruthCert Meta2: a software tool for reviewer-auditable evidence synthesis

## Authors
- Mahmood Ahmad [1,2]
- Niraj Kumar [1]
- Bilaal Dar [3]
- Laiba Khan [1]
- Andrew Woo [4]
- Corresponding author: Andrew Woo (andy2709w@gmail.com)

## Affiliations
1. Royal Free Hospital
2. Tahir Heart Institute Rabwah
3. King's College Medical School
4. St George's Medical School

## Abstract
**Background:** Bias correction alone is not enough when multiple analytic perspectives disagree. TruthCert Meta2 extends denominator-first meta-analysis with explicit governance so that disagreement itself becomes part of the output rather than hidden in analyst judgment.

**Methods:** Meta2 combines the denominator-first delta engine with a question contract, bias decomposition, three independent witnesses (classic, denominator-corrected, and selection-weighted), conservative arbitration, and decision-regret scoring. The repository includes simulations, tests, and a full paper draft.

**Results:** Local materials document topic-level coverage and regret, node-level audit capsules, witness disagreement patterns, and a real-data demonstration showing how arbitration widens uncertainty when registry-derived silence is non-negligible.

**Conclusions:** Meta2 should be described as a governance overlay for denominator-first evidence synthesis, explicitly prioritizing conservative uncertainty inflation over overconfident correction.

## Keywords
publication bias; registry denominators; governance; witness arbitration; decision regret; software tool

## Introduction
The project answers a practical reviewer question: what should a decision-support system do when reasonable analytic witnesses disagree? Instead of hiding that disagreement, Meta2 makes it auditable through node capsules and deterministic governance rules.

The key comparator is a fair publication-only random-effects workflow, not a straw-man baseline. This framing is already built into the local paper and should be preserved in the F1000 version.

The manuscript structure below is deliberately aligned to common open-software review requests: the rationale is stated explicitly, at least one runnable example path is named, local validation artifacts are listed, and conclusions are bounded to the functions and outputs documented in the repository.

## Methods
### Software architecture and workflow
The repository includes inherited Phase 1 engines plus governance modules for contracts, bias decomposition, selection witnesses, witness panels, arbitration, calibration, and regret scoring.

### Installation, runtime, and reviewer reruns
The local implementation is packaged under `C:\Models\truthcert-meta2-prototype`. The manuscript identifies the local entry points, dependency manifest, fixed example input, and expected saved outputs so that reviewers can rerun the documented workflow without reconstructing it from scratch.

- Entry directory: `C:\Models\truthcert-meta2-prototype`.
- Detected documentation entry points: `README.md`, `f1000_artifacts/tutorial_walkthrough.md`.
- Detected environment capture or packaging files: `requirements.txt`.
- Named worked-example paths in this draft: `paper/MANUSCRIPT_PLOS_ONE_TRUTHCERT.md` as the main narrative source; `configs/suite_12topics_meta2.json` for the packaged simulation suite; `outputs/runs/` and `node_capsules.jsonl` for audit-ready outputs.
- Detected validation or regression artifacts: `f1000_artifacts/validation_summary.md`, `tests/test_applied_example.py`, `tests/test_arbitration_conservative.py`, `tests/test_calibration_not_worse.py`, `tests/test_endpoint_reporting.py`, `tests/test_regret_improvement.py`, `tests/test_reproducibility.py`.
- Detected example or sample data files: `f1000_artifacts/example_dataset.csv`.

### Worked examples and validation materials
**Example or fixed demonstration paths**
- `paper/MANUSCRIPT_PLOS_ONE_TRUTHCERT.md` as the main narrative source.
- `configs/suite_12topics_meta2.json` for the packaged simulation suite.
- `outputs/runs/` and `node_capsules.jsonl` for audit-ready outputs.

**Validation and reporting artifacts**
- `tests/test_arbitration_conservative.py`, `test_regret_improvement.py`, and `test_calibration_not_worse.py`.
- Deterministic seeding and reproducibility checks.
- Per-topic metrics and audit-capsule outputs documenting disagreement handling.

### Typical outputs and user-facing deliverables
- Witness-specific and arbitrated intervals.
- Decision-regret and coverage summaries across simulated topics.
- Node-level audit capsules for governance review.

### Reviewer-informed safeguards
- Provides a named example workflow or fixed demonstration path.
- Documents local validation artifacts rather than relying on unsupported claims.
- Positions the software against existing tools without claiming blanket superiority.
- States limitations and interpretation boundaries in the manuscript itself.
- Requires explicit environment capture and public example accessibility in the released archive.

## Review-Driven Revisions
This draft has been tightened against recurring open peer-review objections taken from the supplied reviewer reports.
- Reproducibility: the draft names a reviewer rerun path and points readers to validation artifacts instead of assuming interface availability is proof of correctness.
- Validation: claims are anchored to local tests, validation summaries, simulations, or consistency checks rather than to unsupported assertions of performance.
- Comparators and niche: the manuscript now names the relevant comparison class and keeps the claimed niche bounded instead of implying universal superiority.
- Documentation and interpretation: the text expects a worked example, input transparency, and reviewer-verifiable outputs rather than a high-level feature list alone.
- Claims discipline: conclusions are moderated to the documented scope of TruthCert Meta2 and paired with explicit limitations.

## Use Cases and Results
The software outputs should be described in terms of concrete reviewer-verifiable workflows: running the packaged example, inspecting the generated results, and checking that the reported interpretation matches the saved local artifacts. In this project, the most important result layer is the availability of a transparent execution path from input to analysis output.

Representative local result: `outputs/runs_v2/11bbba3dcee3/global_metrics.csv` reports 12 topics, 50 replications.

### Concrete local quantitative evidence
- `outputs/runs_v2/11bbba3dcee3/global_metrics.csv` reports 12 topics, 50 replications.
- `outputs/runs/11bbba3dcee3/global_metrics.csv` reports 12 topics, 50 replications.
- `paper/MANUSCRIPT_PLOS_ONE_TRUTHCERT.md` reports In the applied example (CD002042, 30-day mortality), 15/37 studies were CT.gov-registered with a 4.1% silent rate; the TruthCert framework produced appropriately wider intervals (risk ratio [RR] 1.02, 95% credible interval [CrI] 0.74-1.39) than classic RE (RR 1.01, 95%.

## Discussion
Representative local result: `outputs/runs_v2/11bbba3dcee3/global_metrics.csv` reports 12 topics, 50 replications.

The strongest reviewer-facing message is that Meta2 is conservative by design. Its purpose is not to force decisive benefit claims, but to formalize epistemic humility when registry denominators and witness disagreement suggest hidden uncertainty.

### Limitations
- Current validation is still dominated by simulation evidence.
- The selection witness is a pragmatic perturbation rather than a fully identifiable selection model.
- Arbitrated intervals may overcover and require further calibration.

## Software Availability
- Local source package: `truthcert-meta2-prototype` under `C:\Models`.
- Public repository: `https://github.com/mahmood726-cyber/truthcert-meta2`.
- Public source snapshot: Fixed public commit snapshot available at `https://github.com/mahmood726-cyber/truthcert-meta2/tree/de3d284fd242760317f34e46af47d02bf58f2bd1`.
- DOI/archive record: No project-specific DOI or Zenodo record URL was detected locally; archive registration pending.
- Environment capture detected locally: `requirements.txt`.
- Reviewer-facing documentation detected locally: `README.md`, `f1000_artifacts/tutorial_walkthrough.md`.
- Reproducibility walkthrough: `f1000_artifacts/tutorial_walkthrough.md` where present.
- Validation summary: `f1000_artifacts/validation_summary.md` where present.
- Reviewer rerun manifest: `F1000_Reviewer_Rerun_Manifest.md`.
- Multi-persona review memo: `F1000_MultiPersona_Review.md`.
- Concrete submission-fix note: `F1000_Concrete_Submission_Fixes.md`.
- License: see the local `LICENSE` file.

## Data Availability
All simulation configurations, outputs, and applied-example materials are stored locally in the project tree. No restricted patient-level data are included.

## Reporting Checklist
Real-peer-review-aligned checklist: `F1000_Submission_Checklist_RealReview.md`.
Reviewer rerun companion: `F1000_Reviewer_Rerun_Manifest.md`.
Companion reviewer-response artifact: `F1000_MultiPersona_Review.md`.
Project-level concrete fix list: `F1000_Concrete_Submission_Fixes.md`.

## Declarations
### Competing interests
The authors declare that no competing interests were disclosed.

### Grant information
No specific grant was declared for this manuscript draft.

### Author contributions (CRediT)
| Author | CRediT roles |
|---|---|
| Mahmood Ahmad | Conceptualization; Software; Validation; Data curation; Writing - original draft; Writing - review and editing |
| Niraj Kumar | Conceptualization |
| Bilaal Dar | Conceptualization |
| Laiba Khan | Conceptualization |
| Andrew Woo | Conceptualization |

### Acknowledgements
The authors acknowledge contributors to open statistical methods, reproducible research software, and reviewer-led software quality improvement.

## References
1. DerSimonian R, Laird N. Meta-analysis in clinical trials. Controlled Clinical Trials. 1986;7(3):177-188.
2. Higgins JPT, Thompson SG. Quantifying heterogeneity in a meta-analysis. Statistics in Medicine. 2002;21(11):1539-1558.
3. Viechtbauer W. Conducting meta-analyses in R with the metafor package. Journal of Statistical Software. 2010;36(3):1-48.
4. Page MJ, McKenzie JE, Bossuyt PM, et al. The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. BMJ. 2021;372:n71.
5. Fay C, Rochette S, Guyader V, Girard C. Engineering Production-Grade Shiny Apps. Chapman and Hall/CRC. 2022.
