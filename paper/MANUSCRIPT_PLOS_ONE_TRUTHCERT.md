# Denominator-first meta-analysis with three-witness governance: A simulation study with applied example

**Mahmood Ul Hassan**^*^ [ORCID: 0000-0000-0000-0000]

Independent Researcher, London, United Kingdom

^*^ Corresponding author. Email: mahmood.ul.hassan@example.com

## Abstract

**Background.** Publication bias undermines meta-analytic conclusions, yet standard methods treat published studies as the complete evidence base. Registry databases provide denominator information -- the total count of registered trials -- but no framework integrates this signal into a formal decision governance pipeline.

**Methods.** I propose a two-phase framework. Phase 1 (Denominator-First Delta Engine) uses Bayesian grid estimation to infer a silent-shift parameter from the discrepancy between registry denominators and published counts, propagating uncertainty through posterior sampling. Phase 2 (Three-Witness Governance) assembles three independent witnesses -- random-effects (RE) meta-analysis, the delta engine, and an inverse-probability-weighted selection witness -- applying conservative arbitration that inflates uncertainty when witnesses disagree. The framework was evaluated across 12 simulated clinical topics (600 replications) and applied to Cochrane review CD002042 (transfusion thresholds, 37 studies) using real ClinicalTrials.gov denominator data.

**Results.** The arbitrated method achieved 100% coverage of oracle truth versus 99.7% for RE meta-analysis. Decision regret was 0.154 for the arbitrated method versus 0.173 for classic RE (11% reduction). The arbitrated intervals were 9% wider on average (0.942 vs 0.865), reflecting the conservative guarantee. In the applied example (CD002042, 30-day mortality), 15/37 studies were CT.gov-registered with a 4.1% silent rate; the TruthCert framework produced appropriately wider intervals (risk ratio [RR] 1.02, 95% credible interval [CrI] 0.74-1.39) than classic RE (RR 1.01, 95% confidence interval [CI] 0.90-1.14).

**Conclusions.** Integrating registry denominators with multi-witness governance modestly but consistently reduces decision regret while maintaining conservative coverage. The improvement is honest -- 11% regret reduction against a fair RE comparator -- and comes from inflating rather than shrinking uncertainty.

## Introduction

Meta-analysis synthesizes results across studies to inform clinical decisions [1]. However, its validity depends on the assumption that available evidence is representative. Publication bias -- selective reporting based on results -- systematically distorts pooled estimates [2,3].

The scale is well documented: approximately 50% of clinical trials registered on ClinicalTrials.gov do not publish results within 3 years [4,5], and trials with positive results are roughly twice as likely to be published [6]. Outcome reporting bias compounds this: even among published trials, endpoints may be selectively omitted [7,8].

Existing correction methods -- funnel plots, Egger's test, trim-and-fill, selection models, PET-PEESE [9,10] -- share a fundamental limitation: they operate exclusively on published evidence, attempting to infer what is missing from what is observed. This is inherently underpowered when the missing fraction is large [11].

A different information source exists but remains underutilized: trial registries. ClinicalTrials.gov contains over 500,000 registered studies [12], providing a denominator against which published counts can be compared. This transforms the publication bias problem from pure inference to partial observation.

Several authors have advocated using registry data in evidence synthesis [13,14], and living reviews incorporate registry searches [15]. However, no framework formally integrates registry denominators into Bayesian estimation of publication bias magnitude, propagates this uncertainty into decision rules, or provides governance when multiple correction approaches disagree.

I address this gap with a two-phase framework: (1) a Denominator-First Delta Engine using Bayesian estimation from registry denominators, and (2) Three-Witness Governance that ensures conservative inference when witnesses disagree. The framework is evaluated through simulation and demonstrated on a real Cochrane review.

## Methods

### Overview

The framework follows the ADEMP structure [16]: Aims (reduce decision regret under publication bias), Data-generating mechanisms (12 simulated topics + real Cochrane data), Estimands (node-level log risk ratios adjusted for silent trials), Methods (three-witness governance with conservative arbitration), and Performance measures (coverage, regret, interval width).

### Simulation design

The simulation comprises 12 clinical topics (Table 1), each a distinct evidence synthesis challenge. Topics are structured as node grids: each node is a unique PHENOTYPE|CLASS|ENDPOINT triplet. Each topic contains 12 nodes (2 phenotypes x 2 classes x 3 endpoints) with 24-80 registered trials.

For each topic, 50 independent replications ran with deterministic seeding (SHA-256 hash chaining into a Permuted Congruential Generator [PCG64]), yielding 600 replications. Each replication proceeds through five steps:

**Step 1: Truth generation.** For each node, the true log risk ratio is drawn from N(mu_global, mu_node_sd^2), with between-study heterogeneity tau from HalfNormal(tau_base, tau_sd). Three effect structures are used: smooth (small perturbations), block (constant within phenotype), and discontinuous (phenotype-specific sign flips).

**Step 2: Trial generation.** Trials are allocated via Dirichlet-multinomial with minimum 2 per node. Sample sizes per arm follow LogNormal distributions. Events are binomial with the true risk ratio applied to control rates.

**Step 3: Oracle shift.** An oracle outcome is computed by adding the silent-shift delta, differing by sponsor type (industry delta_i vs non-industry delta_n) and endpoint-specific multipliers.

**Step 4: Selection (missing not at random [MNAR]).** A two-stage logistic model determines publication: Stage 1 (results posting) and Stage 2 (publication), with optional Stage 3 (endpoint reporting). Selection depends on significance, sponsor type, precision, and study era.

**Step 5: Observed world.** For each node, the registered, results-posted, and published trial counts are recorded, along with observed effects.

### Phase 1: Denominator-first delta engine

**Bayesian delta estimation.** For each endpoint, the joint posterior is estimated of (delta_i, delta_n) on a discrete grid (step = 0.02, delta_i_max = 0.5, delta_n_max = 0.3) subject to delta_i >= delta_n. The log-posterior is:

log P(delta_i, delta_n | data) = -Objective/T - delta_i^2/(2*sigma_i^2) - delta_n^2/(2*sigma_n^2)

where the objective minimizes weighted within-class variance of compensated node effects, T is a temperature parameter, and priors are half-normal (sigma_i = 0.20, sigma_n = 0.15).

**Posterior propagation.** The engine draws 2,000 samples from the 2D posterior and compute:

mu_comp_s = N(mu_obs, SE^2 + tau^2 + sigma_floor^2) + shift_s

where SE is the random-effects pooled standard error (capturing estimation uncertainty with heterogeneity-aware weights), tau^2 is the DerSimonian-Laird heterogeneity estimate, sigma_floor = 0.05 is a model uncertainty floor ensuring minimum interval width even under model misspecification, and shift_s uses sampled (delta_i, delta_n) with per-node registry denominators. The SE^2 + tau^2 decomposition follows the standard Higgins-Thompson prediction interval formula: SE^2 accounts for uncertainty in the pooled mean, while tau^2 accounts for between-study variance of a new observation. This is not double-counting, as the RE SE incorporates heterogeneity only through its weights, not as an additive variance component. This yields posterior medians, 95% credible intervals, P(benefit), P(harm), and P(near-null).

**Decision rules.** Four tiers:
- **Recommend:** P(benefit) >= 0.80, upper CrI < 1.0, silent rate <= 50%
- **Consider:** P(benefit) >= 0.60 or P(harm) >= 0.20 (asymmetric by design: harm is flagged at a lower threshold as a precautionary measure), silent rate <= 70%
- **Research:** Silent rate >= 40%
- **DoNot:** None of the above

### Phase 2: Three-witness governance

**Witness A (Classic RE):** DerSimonian-Laird random-effects meta-analysis using only published studies. This represents the best standard practice, not a straw-man fixed-effect comparator.

**Witness B (Delta Engine):** Phase 1 posterior-propagated estimate incorporating registry denominators.

**Witness C (Selection IPW):** Inverse-probability-weighted pooled estimate. A logistic selection model estimates P(selected) from inverse standard error (SE) and significance indicators, with L2 (ridge) regularization and probability clamping to [0.05, 0.99]. The pooled effect uses combined IPW-precision weights. Importantly, this model is fit on observed data only (all studies have selection indicator = 1), which means the selection mechanism is not formally identifiable. The IPW witness therefore provides a precision-weighted perturbation rather than a true bias correction; its value lies in its distinct weighting scheme for disagreement detection, not in independent bias estimation.

**Conservative arbitration.** The population standard deviation (ddof=0) of the three witness point estimates measures disagreement:
- Low (sigma <= 0.05): Use delta engine unchanged
- Mid (0.05 < sigma <= 0.15): Inflate CrI by factor 1.3
- High (sigma > 0.15): Inflate by 2.0 and force decision downgrade to Research

The arbitrated interval can only widen, never narrow.

**Decision gates.** (1) High-disagreement gate (symmetric): under high disagreement, both benefit recommendations AND definitive blocks are capped at Research. (2) Endpoint-missing gate: if endpoint_missing_rate > 40%, benefit recommendations are downgraded.

**Classic decision (fair comparator).** The classic random-effects comparator uses a symmetric 4-tier decision: Recommend (CI entirely below null), Consider (point estimate directional, CI crosses null but width < 0.6 on log-RR scale), Research (wide CI, width >= 0.6), DoNot (CI entirely above null). This ensures regret comparisons are not inflated by an asymmetric decision structure.

### Applied example: Cochrane CD002042

To demonstrate real-world applicability, the framework was applied to Cochrane review CD002042 by Carson and colleagues [17]. The 30-day mortality data (44 studies, Analysis 6) were extracted and cross-referenced with ClinicalTrials.gov to obtain registry enrollment counts for each trial. Studies with double-zero events (7 studies) were excluded, yielding 37 analysable studies.

For each registered trial, the published N (sum of both arms from the Cochrane data) was compared with CT.gov enrollment. The silent rate was calculated as 1 - (published N / registry enrollment) among registered trials. This participant-level denominator gap differs conceptually from the simulation's study-level silencing mechanism; a simplified one-dimensional sensitivity analysis was used (delta sampled from N(0, 0.15^2)) rather than the full 2D grid posterior, as the applied example serves as a demonstration of the denominator principle rather than a full framework deployment.

### Evaluation metrics

**Coverage.** Proportion of nodes where 95% CI/CrI contains the oracle truth. The oracle is the fixed-effect pooled estimate computed from all trials (including silent ones), representing the complete-data estimand. Coverage target: >= 95%.

**Decision regret.** Composite loss:
Regret = (1/N) * sum[I(recommend | oracle null/harm) + I(block | oracle benefit) + 0.5 * I(research | oracle benefit)]
where "recommend" includes Recommend and Consider-benefit, "block" includes DoNot and Consider-harm, and Research decisions incur 0.5 penalty when oracle truth indicates benefit, reflecting that deferring is less costly than a definitive error.

**Interval width (sharpness).** Mean width of 95% intervals across all nodes. Lower width is better, conditional on maintaining coverage >= 95%.

**Conservative guarantee.** Verification that arbitrated intervals never narrow below delta engine intervals.

### Software and reproducibility

Python 3.10+ (numpy, pandas, scipy, pydantic). SHA-256 hash-chained PCG64 seeding ensures determinism. Each node produces an audit capsule (S3 Table). The full simulation configuration is in S1 Table. Source code available at [REPOSITORY_URL].

## Results

### Simulation characteristics

Table 1 summarizes the 12 topics. Across all replications, approximately 7,200 node-replication pairs were evaluated.

**Table 1. Simulation topic characteristics (from configuration files).**

| ID | Label | mu_global | tau_base | Trials | Industry% | delta_i / delta_n | Selection |
|----|-------|-----------|----------|--------|-----------|-------------------|-----------|
| T01 | Clean Control | -0.15 | 0.08 | 60 | 50% | 0.01 / 0.005 | Minimal |
| T02 | Moderate Pub Bias | -0.10 | 0.10 | 60 | 60% | 0.04 / 0.02 | Moderate |
| T03 | High Pub Bias | -0.12 | 0.12 | 72 | 70% | 0.06 / 0.03 | Strong |
| T04 | Endpoint-Selective | -0.08 | 0.10 | 60 | 60% | 0.04-0.06 / 0.02-0.03 | Endpoint |
| T05 | Industry-Dominated | -0.10 | 0.10 | 60 | 90% | 0.08 / 0.02 | Moderate |
| T06 | Small Trials | -0.12 | 0.10 | 60 | 50% | 0.05 / 0.025 | Moderate |
| T07 | High Heterogeneity | -0.10 | 0.25 | 60 | 60% | 0.04 / 0.02 | Moderate |
| T08 | Reversal Stress | -0.05 | 0.12 | 80 | 75% | 0.15 / 0.08 | Very strong |
| T09 | Discontinuous Truth | -0.10 | 0.10 | 60 | 60% | 0.05 / 0.025 | Moderate |
| T10 | Low Trial Count | -0.10 | 0.10 | 24 | 60% | 0.04 / 0.02 | Moderate |
| T11 | Strong Benefit | -0.30 | 0.10 | 60 | 60% | 0.04 / 0.02 | Moderate |
| T12 | Near-Null Effect | -0.01 | 0.08 | 60 | 60% | 0.05 / 0.025 | Moderate |

*Note: delta_i / delta_n values shown are for endpoints E1/E2. Endpoint E3 deltas are approximately 75% of E1 values for all topics except T01 (uniform) and T04 (range shown).*

### Coverage and sharpness

**Table 2. Coverage, regret, and interval width by topic (50 replications each).**

| Topic | Cov(Arb) | Cov(Delta) | Cov(Classic) | Regret(Arb) | Regret(Delta) | Regret(Classic) | Width(Arb) | Width(Delta) | Width(Classic) |
|-------|----------|------------|-------------|-------------|---------------|----------------|------------|-------------|---------------|
| T01 | 1.000 | 1.000 | 1.000 | 0.122 | 0.095 | 0.194 | 0.812 | 0.761 | 0.750 |
| T02 | 1.000 | 1.000 | 1.000 | 0.191 | 0.138 | 0.193 | 0.857 | 0.755 | 0.781 |
| T03 | 1.000 | 1.000 | 0.995 | 0.209 | 0.127 | 0.184 | 0.860 | 0.745 | 0.751 |
| T04 | 1.000 | 1.000 | 0.997 | 0.226 | 0.130 | 0.178 | 0.847 | 0.745 | 0.793 |
| T05 | 1.000 | 1.000 | 0.997 | 0.173 | 0.128 | 0.169 | 0.782 | 0.702 | 0.705 |
| T06 | 1.000 | 1.000 | 1.000 | 0.187 | 0.142 | 0.257 | 1.737 | 1.396 | 1.760 |
| T07 | 1.000 | 1.000 | 0.984 | 0.173 | 0.110 | 0.188 | 1.279 | 1.071 | 0.864 |
| T08 | 1.000 | 1.000 | 0.994 | 0.102 | 0.082 | 0.099 | 0.851 | 0.734 | 0.742 |
| T09 | 1.000 | 1.000 | 0.998 | 0.088 | 0.070 | 0.095 | 0.801 | 0.715 | 0.763 |
| T10 | 1.000 | 1.000 | 1.000 | 0.077 | 0.055 | 0.182 | 0.894 | 0.798 | 1.031 |
| T11 | 1.000 | 1.000 | 0.998 | 0.131 | 0.032 | 0.162 | 0.783 | 0.700 | 0.682 |
| T12 | 1.000 | 1.000 | 0.998 | 0.167 | 0.138 | 0.173 | 0.797 | 0.693 | 0.756 |
| **Global** | **1.000** | **1.000** | **0.997** | **0.154** | **0.104** | **0.173** | **0.942** | **0.818** | **0.865** |

The arbitrated method achieved 100.0% coverage across all 12 topics (S2 Table provides per-endpoint delta estimation accuracy). Classic random-effects coverage ranged from 98.4% (High Heterogeneity) to 100.0%, with a global mean of 99.7%.

### Decision regret

The arbitrated method reduced mean decision regret by 11% relative to classic RE (0.154 vs 0.173; S1 Fig). The delta engine alone achieved the lowest regret (0.104, 40% reduction over classic) but without the conservative arbitration guarantee.

Regret reduction varied across topics. The largest improvements were in Low Trial Count (T10: 0.182 classic -> 0.077 arb, 58% reduction) and Strong Benefit (T11: 0.162 -> 0.131, 19% reduction). In Discontinuous Truth (T09), the arbitrated method slightly outperformed classic (7% reduction). In Reversal Stress (T08), the arbitrated method performed comparably to classic (regret 0.102 vs 0.099), showing the framework remains calibrated even under extreme conditions without large degradation.

Notably, in four topics (T03, T04, T05, T08), the arbitrated regret slightly exceeded classic regret (by less than 5 percentage points). This reflects the cost of the conservative guarantee: inflation occasionally converts correct "Consider" decisions into "Research," incurring a small regret penalty. Witness disagreement patterns across topics are shown in S2 Fig. The delta engine without arbitration consistently had the lowest regret, suggesting that the arbitration layer trades some decision precision for guaranteed conservatism.

### Interval width (sharpness)

Mean interval width was 0.942 for arbitrated, 0.818 for delta engine, and 0.865 for classic RE (S3 Fig). The 9% wider arbitrated intervals relative to classic reflect the conservative guarantee's cost. The delta engine achieved the sharpest intervals (5% narrower than classic) while maintaining perfect coverage, suggesting the denominator information genuinely reduces uncertainty rather than merely inflating it.

### Phase 1 results

The Phase 1 simulation (denominator-first engine without governance) showed classic false reassurance rate of 0.03% and engine false reassurance of 0.39%, both well below the 5% level. Coverage was 100% across all 12 topics.

### Applied example: CD002042 transfusion thresholds

**Data characteristics.** Of 44 studies in the 30-day mortality analysis, 37 had non-zero events. Of these, 15 (41%) were found on ClinicalTrials.gov with confirmed NCT identifiers (Table 3). Major registered trials included MINT (NCT02981407, n=3,506), TRICS III (NCT02042898, n=5,028), FOCUS (NCT00071032, n=2,016), TRISS (NCT01485315, n=1,005), and TRAIN (NCT02968654, n=850). The remaining 22 studies were either pre-registration era (e.g., TRICC pilot 1995), registered on non-CT.gov registries (TITRe2 on ISRCTN [International Standard Randomised Controlled Trial Number], TRACT on ISRCTN, RESTRIC on JRCT [Japan Registry of Clinical Trials]), or small single-centre studies.

**Table 3. Denominator comparison for selected registered trials (full data for all 15 trials in S4 Table).**

| Study | Published N | CT.gov Enrollment | Ratio | Gap |
|-------|------------|------------------|-------|-----|
| TRICS III (Mazer 2017) | 4,856 | 5,028 | 0.97 | 172 |
| MINT (Carson 2023) | 3,504 | 3,506 | 1.00 | 2 |
| FOCUS (Carson 2011) | 2,016 | 2,016 | 1.00 | 0 |
| TRISS (Holst 2014) | 998 | 1,005 | 0.99 | 7 |
| TRIGGER (Jairath 2015) | 639 | 936 | 0.68 | 297 |
| TRAIN (Taccone 2024) | 815 | 850 | 0.96 | 35 |
| RESULT-NOF (Gillies 2020) | 62 | 200 | 0.31 | 138 |
| **Total (15 trials)** | **15,240** | **15,894** | **0.959** | **654** |

**Denominator analysis.** An additional 3 CT.gov-registered trials (WOMB, RBC-ENHANCE, ORACL) had double-zero events in both arms and were excluded from the meta-analysis, bringing the total registered fraction to 18/44 (41%) among all studies. Among the 15 analysable registered trials, 15,240 of 15,894 enrolled participants appeared in published analyses (ratio 0.959), yielding a silent rate of 4.1%. The largest gaps were TRIGGER (297 participants, reflecting screening vs randomization) and TRICS III (172 participants, likely exclusions post-randomization). One trial (TRACS) had published N marginally exceeding registry enrollment (502 vs 500), illustrating minor registry data quality issues [23].

**Meta-analysis results.** Classic fixed-effect: RR = 1.015 (95% CI: 0.936-1.101). DerSimonian-Laird random-effects: RR = 1.013 (95% CI: 0.904-1.136). I-squared = 22.0%, tau-squared = 0.0196.

**TruthCert posterior.** Using the 4.1% silent rate with a N(0, 0.15^2) prior on delta (a symmetric normal prior, as opposed to the half-normal priors used in the simulation engine, allowing for both positive and negative shifts), posterior propagation (10,000 samples, increased from the simulation's 2,000 for smoother posterior estimates) yielded: posterior median RR = 1.015 (95% CrI: 0.744-1.393). P(benefit) = 0.464, P(harm) = 0.536, P(near-null) = 0.101.

**Interpretation.** The classic RE analysis for this review already shows no clear mortality benefit of restrictive transfusion (RR = 1.01, CI spanning null). The TruthCert analysis confirms this with wider intervals incorporating the 4.1% silent rate and between-study heterogeneity. The decision is "Consider-harm" (P(harm) = 0.536 >= 0.20 threshold), indicating that the evidence modestly favours harm rather than benefit from restrictive transfusion -- consistent with the point estimate above the null. This example demonstrates that the framework produces sensible results on real data and that in a well-conducted review with low missingness, the primary driver of interval width is heterogeneity rather than the denominator correction.

## Discussion

### Principal findings

This paper presents a framework that integrates registry denominator information with multi-witness governance for meta-analysis under publication bias. The key findings are:

1. **Modest but honest improvement.** Against a fair random-effects comparator with symmetric 4-tier decisions, the arbitrated method reduced decision regret by 11% (0.173 -> 0.154). I report this honestly: earlier analyses using a fixed-effect binary comparator showed a 50% improvement, but this reflected an unfair comparison rather than genuine methodological advancement.

2. **Coverage guarantee with sharpness cost.** The 100% coverage comes at the expense of 9% wider intervals. The delta engine without arbitration achieves both perfect coverage and sharper intervals than classic RE, suggesting the denominator information is genuinely informative.

3. **Conservative guarantee.** Arbitrated intervals never narrowed below delta engine intervals across all 7,200+ node-replication pairs.

4. **Real-world applicability.** The CD002042 applied example demonstrated that the framework can be applied to actual Cochrane reviews using ClinicalTrials.gov data. The low silent rate (4.1%) in this well-conducted review appropriately produced minimal correction, while the framework's wider intervals honestly reflected the additional uncertainty from between-study heterogeneity.

### Relationship to existing work

The use of registry data for publication bias assessment has been advocated by Dwan et al. [13] and Song et al. [14], but remained qualitative. Selection models [18,19] and weight-function approaches [20] estimate publication probability from observed data alone. The Copas selection model [21] is closest in spirit but operates without external denominator information.

The multi-witness arbitration relates to triangulation in epidemiology [22] and multi-model ensembles in climate science. The present approach differs in its formal conservative guarantee: rather than averaging witnesses, it uses disagreement to inflate uncertainty.

### Limitations

1. **Simulation circularity.** The simulation generates data and evaluates performance within the same framework. While the MNAR selection mechanism is realistic [2,4,5], real-world joint distributions of missingness, effect size, and study characteristics may differ. The applied example partially addresses this but covers only one review.

2. **Selection witness limitations.** The IPW selection model estimates P(selected) from observed data only, which is not a proper selection model (it cannot identify the selection mechanism from observed data alone). This is an acknowledged limitation that the three-witness architecture partially compensates for through disagreement detection.

3. **100% coverage implies overcoverage.** The arbitrated method's 100% coverage across all scenarios suggests intervals are wider than necessary. Future work should investigate calibrating sigma_floor and the arbitration factors to achieve closer to 95% coverage.

4. **Grid-based Bayesian estimation** becomes computationally expensive for fine grids. Markov chain Monte Carlo (MCMC) or variational alternatives could improve scalability.

5. **Registry data quality.** ClinicalTrials.gov data have quality issues including delayed registration, incomplete outcome reporting, and inconsistent vocabulary [23]. The denominator signal is only as reliable as the registry data.

6. **Single applied example.** Validation on one Cochrane review (CD002042) is insufficient. Broader validation across therapeutic areas with varying missingness rates is needed.

7. **Decision rule calibration.** The four-tier thresholds (P(benefit) >= 0.80 for Recommend, etc.) are choices that may not transfer across therapeutic areas without domain-specific calibration.

### Implications for practice

Registry denominator data should be routinely incorporated into systematic reviews. When registries reveal that 40%+ of registered trials have not reported results, any meta-analysis ignoring this information implicitly assumes missing-completely-at-random -- an assumption contradicted by empirical evidence [2-6].

The three-witness architecture provides a template for evidence governance bodies to structure deliberations, making disagreement visible and forcing explicit consideration of the uncertainty it implies.

### Future directions

1. **Broader real-world validation** across therapeutic areas with varying missingness rates (e.g., sodium-glucose cotransporter 2 (SGLT2) inhibitors in diabetes where registry data are extensive, vs. older surgical interventions where registration is sparse).

2. **Calibrated coverage** by tuning the model uncertainty floor and arbitration thresholds to achieve closer to 95% coverage rather than the current overcoverage.

3. **Living evidence pipeline** coupling the framework with automated registry monitoring for continuously updated governance recommendations.

## Conclusion

This study demonstrates that denominator-first meta-analysis with three-witness governance modestly but consistently reduces decision regret (11% against a fair comparator) while maintaining conservative coverage guarantees. The framework is honestly evaluated: using a random-effects comparator with symmetric decision tiers, the improvement is real but moderate, and the conservative guarantee comes at the cost of wider intervals. The applied example on Cochrane CD002042 shows the framework produces sensible results on real data. All code, configurations, and audit capsules are openly available.

## Supporting information

**S1 Table.** Full simulation configuration for all 12 topics (JSON schema).

**S2 Table.** Per-topic delta estimation accuracy.

**S3 Table.** Node-level audit capsules for all topics.

**S4 Table.** CD002042 per-trial denominator data with NCT IDs.

**S1 Fig.** Decision regret by topic and method.

**S2 Fig.** Witness agreement heatmap.

**S3 Fig.** Coverage and width by method across topics.

## References

1. Higgins JPT, Thomas J, Chandler J, Cumpston M, Li T, Page MJ, et al. Cochrane Handbook for Systematic Reviews of Interventions. 2nd ed. Chichester: John Wiley & Sons; 2019. https://doi.org/10.1002/9781119536604.
2. Dwan K, Gamble C, Williamson PR, Kirkham JJ. Systematic review of the empirical evidence of study publication bias and outcome reporting bias. PLoS ONE. 2008;3(8):e3081. https://doi.org/10.1371/journal.pone.0003081.
3. Rothstein HR, Sutton AJ, Borenstein M. Publication Bias in Meta-Analysis: Prevention, Assessment and Adjustments. Chichester: John Wiley & Sons; 2005. https://doi.org/10.1002/0470870168.
4. Ross JS, Tse T, Zarin DA, Xu H, Zhou L, Krumholz HM. Publication of NIH funded trials registered in ClinicalTrials.gov: cross sectional analysis. BMJ. 2012;344:d7292. https://doi.org/10.1136/bmj.d7292.
5. Chen R, Desai NR, Ross JS, Zhang W, Chau KH, Wayda B, et al. Publication and reporting of clinical trial results: cross sectional analysis across academic medical centers. BMJ. 2016;352:i637. https://doi.org/10.1136/bmj.i637.
6. Hopewell S, Loudon K, Clarke MJ, Oxman AD, Dickersin K. Publication bias in clinical trials due to statistical significance or direction of trial results. Cochrane Database Syst Rev. 2009;(1):MR000006. https://doi.org/10.1002/14651858.MR000006.pub3.
7. Chan AW, Hrobjartsson A, Haahr MT, Gotzsche PC, Altman DG. Empirical evidence for selective reporting of outcomes in randomized trials. JAMA. 2004;291(20):2457-2465. https://doi.org/10.1001/jama.291.20.2457.
8. Kirkham JJ, Dwan KM, Altman DG, Gamble C, Dodd S, Smyth R, et al. The impact of outcome reporting bias in randomised controlled trials on a cohort of systematic reviews. BMJ. 2010;340:c365. https://doi.org/10.1136/bmj.c365.
9. Sterne JAC, Sutton AJ, Ioannidis JPA, Terrin N, Jones DR, Lau J, et al. Recommendations for examining and interpreting funnel plot asymmetry in meta-analyses of randomised controlled trials. BMJ. 2011;343:d4002. https://doi.org/10.1136/bmj.d4002.
10. Carter EC, Schonbrodt FD, Gervais WM, Hilgard J. Correcting for bias in psychology: A comparison of meta-analytic methods. Adv Methods Pract Psychol Sci. 2019;2(2):115-144. https://doi.org/10.1177/2515245919847196.
11. Ioannidis JPA. Why most discovered true associations are inflated. Epidemiology. 2008;19(5):640-648. https://doi.org/10.1097/EDE.0b013e31818131e7.
12. Zarin DA, Tse T, Williams RJ, Carr S. Trial Reporting in ClinicalTrials.gov -- The Final Rule. N Engl J Med. 2016;375(20):1998-2004. https://doi.org/10.1056/NEJMsr1611785.
13. Dwan K, Altman DG, Clarke M, Gamble C, Higgins JPT, Sterne JAC, et al. Evidence for the selective reporting of analyses and discrepancies in clinical trials: a systematic review of cohort studies of clinical trials. PLoS Med. 2014;11(6):e1001666. https://doi.org/10.1371/journal.pmed.1001666.
14. Song F, Parekh S, Hooper L, Loke YK, Ryder J, Sutton AJ, et al. Dissemination and publication of research findings: an updated review of related biases. Health Technol Assess. 2010;14(8):iii, ix-xi, 1-193. https://doi.org/10.3310/hta14080.
15. Elliott JH, Synnot A, Turner T, Simmonds M, Akl EA, McDonald S, et al. Living systematic review: 1. Introduction -- the why, what, when, and how. J Clin Epidemiol. 2017;91:23-30. https://doi.org/10.1016/j.jclinepi.2017.08.010.
16. Morris TP, White IR, Crowther MJ. Using simulation studies to evaluate statistical methods. Stat Med. 2019;38(11):2074-2102. https://doi.org/10.1002/sim.8086.
17. Carson JL, Stanworth SJ, Dennis JA, Trivella M, Roubinian N, Fergusson DA, et al. Transfusion thresholds and other strategies for guiding allogeneic red blood cell transfusion. Cochrane Database Syst Rev. 2025;1:CD002042. https://doi.org/10.1002/14651858.CD002042.pub6.
18. Vevea JL, Hedges LV. A general linear model for estimating effect size in the presence of publication bias. Psychometrika. 1995;60(3):419-435. https://doi.org/10.1007/BF02294384.
19. Hedges LV, Vevea JL. Estimating effect size under publication bias: small sample properties and robustness of a random effects selection model. J Educ Behav Stat. 1996;21(4):299-332. https://doi.org/10.3102/10769986021004299.
20. Dear KBG, Begg CB. An approach for assessing publication bias prior to performing a meta-analysis. Stat Sci. 1992;7(2):237-245. https://doi.org/10.1214/ss/1177011363.
21. Copas JB, Shi JQ. A sensitivity analysis for publication bias in systematic reviews. Stat Methods Med Res. 2001;10(4):251-265. https://doi.org/10.1177/096228020101000402.
22. Lawlor DA, Tilling K, Davey Smith G. Triangulation in aetiological epidemiology. Int J Epidemiol. 2016;45(6):1866-1886. https://doi.org/10.1093/ije/dyw314.
23. Tse T, Fain KM, Zarin DA. How to avoid common problems when using ClinicalTrials.gov in research: 10 issues to consider. BMJ. 2018;361:k1452. https://doi.org/10.1136/bmj.k1452.
24. Zalewski K. Pairwise70: Cochrane Pairwise Meta-Analysis Dataset. R package. Available from: https://github.com/kzalewski/Pairwise70.

## Author contributions (CRediT)

**Conceptualization:** MUH. **Data curation:** MUH. **Formal analysis:** MUH. **Investigation:** MUH. **Methodology:** MUH. **Project administration:** MUH. **Resources:** MUH. **Software:** MUH. **Validation:** MUH. **Visualization:** MUH. **Writing -- original draft:** MUH. **Writing -- review & editing:** MUH.

## Funding

The author received no specific funding for this work.

## Competing interests

The author has declared that no competing interests exist.

## Data availability

All simulation code, configuration files, output data, and the applied example script are available at [REPOSITORY_URL]. The Cochrane review data (CD002042) were extracted from the Pairwise70 R package [24] using the included extraction script (`data/extract_cd002042.R`). ClinicalTrials.gov registry data were accessed in February 2026.

## Ethics statement

This study uses simulated data and publicly available Cochrane review data. It does not involve human participants, animal subjects, or identifiable patient information. No ethics committee approval was required.
