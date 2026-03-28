Mahmood Ahmad
Tahir Heart Institute
mahmood.ahmad2@nhs.net

TruthCert Meta2: Governance Overlay for Denominator-First Meta-Analysis

Can a governance overlay on denominator-first meta-analysis reduce false reassurance from missing trial results? We developed TruthCert Meta2, extending the delta engine with three-witness arbitration that locks the estimand via a question contract before analysis. The system pools three independent estimates: classic fixed-effect from publications, the Bayesian delta engine correcting registry-to-publication gaps, and an inverse-probability-weighted selection witness for reporting bias. Across 12 simulated topics with 50 replications, the mean difference between arbitrated and oracle estimates was 0.03 (95% CI 0.01-0.06) with coverage at 0.92, exceeding classic coverage of 0.71 and delta coverage of 0.87, while regret fell 34 percent. Sensitivity analyses confirmed the conservative rule never produced intervals narrower than delta alone, preserving monotonic safety across all silence fractions. Structured witness disagreement detection with principled interval inflation provides a viable path toward trustworthy synthesis under selective reporting. However, the framework remains limited to simulated scenarios with known truth, and performance under real-world correlated missingness warrants validation.

Outside Notes

Type: methods
Primary estimand: Mean difference
App: TruthCert Meta2 Prototype
Data: 12 simulated clinical topics, 50 replications each
Code: https://github.com/mahmood726-cyber/truthcert-meta2
Version: 1.0
Validation: DRAFT

References

1. Roever C. Bayesian random-effects meta-analysis using the bayesmeta R package. J Stat Softw. 2020;93(6):1-51.
2. Higgins JPT, Thompson SG, Spiegelhalter DJ. A re-evaluation of random-effects meta-analysis. J R Stat Soc Ser A. 2009;172(1):137-159.
3. Borenstein M, Hedges LV, Higgins JPT, Rothstein HR. Introduction to Meta-Analysis. 2nd ed. Wiley; 2021.

AI Disclosure

This work represents a compiler-generated evidence micro-publication (i.e., a structured, pipeline-based synthesis output). AI is used as a constrained synthesis engine operating on structured inputs and predefined rules, rather than as an autonomous author. Deterministic components of the pipeline, together with versioned, reproducible evidence capsules (TruthCert), are designed to support transparent and auditable outputs. All results and text were reviewed and verified by the author, who takes full responsibility for the content. The workflow operationalises key transparency and reporting principles consistent with CONSORT-AI/SPIRIT-AI, including explicit input specification, predefined schemas, logged human-AI interaction, and reproducible outputs.
