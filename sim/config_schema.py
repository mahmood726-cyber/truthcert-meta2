"""Pydantic configuration schema for the simulation suite."""

from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ── Truth sub-models ──────────────────────────────────────────────────────

class DiscontinuityConfig(BaseModel):
    enabled: bool = False
    type: Literal["phenotype_flip", "node_flip"] = "phenotype_flip"
    magnitude: float = Field(default=0.5, ge=0)


class TruthConfig(BaseModel):
    mu_global: float = -0.1
    node_effect_structure: Literal["block", "smooth", "discontinuous"] = "smooth"
    mu_node_sd: float = Field(default=0.15, ge=0)
    tau_base: float = Field(default=0.1, ge=0)
    tau_sd: float = Field(default=0.03, ge=0)
    discontinuity: DiscontinuityConfig = Field(default_factory=DiscontinuityConfig)


# ── Baseline risk / sample size ───────────────────────────────────────────

class BaselineRiskConfig(BaseModel):
    control_event_rate: Dict[str, List[float]]  # endpoint -> [low, high]


class SampleSizeConfig(BaseModel):
    n_per_arm: List[int] = Field(default=[50, 500], min_length=2, max_length=2)
    size_distribution: Literal["lognormal", "uniform"] = "lognormal"
    size_sigma: float = Field(default=0.8, gt=0)


# ── Missingness sub-models ────────────────────────────────────────────────

class ResultsPostingConfig(BaseModel):
    base_rate: float = Field(default=0.6, ge=0, le=1)
    coef: Dict[str, float]  # industry, signif_benefit, signif_harm, se, post2015


class PublicationConfig(BaseModel):
    base_rate: float = Field(default=0.5, ge=0, le=1)
    coef: Dict[str, float]  # + results_posted


class EndpointReportingConfig(BaseModel):
    enabled: bool = True
    base_rate_by_endpoint: Dict[str, float]
    coef: Dict[str, float]  # industry, signif_benefit, se


class DeltaByEndpointEntry(BaseModel):
    industry: float = Field(ge=0)
    nonindustry: float = Field(ge=0)


class SilentShiftDeltaConfig(BaseModel):
    enabled: bool = True
    delta_by_endpoint: Dict[str, DeltaByEndpointEntry]
    constraint: Literal["industry_ge_nonindustry", "none"] = "industry_ge_nonindustry"
    multiplier_by_endpoint: Dict[str, float]


class MissingnessConfig(BaseModel):
    results_posting: ResultsPostingConfig
    publication: PublicationConfig
    endpoint_reporting: EndpointReportingConfig
    silent_shift_delta: SilentShiftDeltaConfig


# ── Engine sub-models ─────────────────────────────────────────────────────

class DeltaGridConfig(BaseModel):
    di_max: float = Field(default=0.5, gt=0)
    dn_max: float = Field(default=0.3, gt=0)
    step: float = Field(default=0.02, gt=0)


class DeltaPriorConfig(BaseModel):
    type: Literal["half_normal"] = "half_normal"
    sigma_industry: float = Field(default=0.2, gt=0)
    sigma_nonindustry: float = Field(default=0.15, gt=0)


class DeltaBayesConfig(BaseModel):
    grid: DeltaGridConfig = Field(default_factory=DeltaGridConfig)
    prior: DeltaPriorConfig = Field(default_factory=DeltaPriorConfig)
    temperature_T: float = Field(default=1.0, gt=0)
    grouping: Literal["class", "phenotype", "endpoint"] = "class"


class PropagationConfig(BaseModel):
    n_posterior_samples: int = Field(default=2000, ge=1)
    include_mu_obs_uncertainty: bool = True
    model_unc_floor: float = Field(default=0.05, ge=0)


class RecommendRule(BaseModel):
    p_benefit: float = Field(default=0.80, ge=0, le=1)
    upper: float = Field(default=1.0, gt=0)
    silent_rate_max: float = Field(default=0.50, ge=0, le=1)


class ConsiderRule(BaseModel):
    p_benefit: float = Field(default=0.60, ge=0, le=1)
    p_harm: float = Field(default=0.20, ge=0, le=1)
    silent_rate_max: float = Field(default=0.70, ge=0, le=1)


class ResearchRule(BaseModel):
    silent_rate_min: float = Field(default=0.40, ge=0, le=1)


class DecisionRuleConfig(BaseModel):
    benefit_threshold: float = Field(default=1.0, gt=0)
    recommend: RecommendRule = Field(default_factory=RecommendRule)
    consider: ConsiderRule = Field(default_factory=ConsiderRule)
    research: ResearchRule = Field(default_factory=ResearchRule)


class ArbitrationConfig(BaseModel):
    """Configurable arbitration thresholds for the governance layer."""
    thresh_low: float = Field(default=0.05, ge=0)
    thresh_high: float = Field(default=0.15, ge=0)
    inflate_mid: float = Field(default=1.3, ge=1.0)
    inflate_high: float = Field(default=2.0, ge=1.0)
    endpoint_missing_threshold: float = Field(default=0.40, ge=0, le=1)


class EngineConfig(BaseModel):
    delta_bayes: DeltaBayesConfig = Field(default_factory=DeltaBayesConfig)
    propagation: PropagationConfig = Field(default_factory=PropagationConfig)
    decision_rule: DecisionRuleConfig = Field(default_factory=DecisionRuleConfig)
    arbitration: ArbitrationConfig = Field(default_factory=ArbitrationConfig)
    ablation_modes: List[str] = ["denom_only", "delta_only"]


# ── Top-level models ──────────────────────────────────────────────────────

class NodeGridConfig(BaseModel):
    phenotypes: List[str] = Field(min_length=1)
    classes: List[str] = Field(min_length=1)
    endpoints: List[str] = Field(min_length=1)


class TrialCountConfig(BaseModel):
    n_trials_total: int = Field(default=60, ge=1)
    min_trials_per_node: int = Field(default=2, ge=1)
    dispersion: float = Field(default=1.0, gt=0)


class SponsorConfig(BaseModel):
    industry_rate: float = Field(default=0.6, ge=0, le=1)


class TopicConfig(BaseModel):
    topic_id: str
    label: str
    node_grid: NodeGridConfig
    trial_count: TrialCountConfig
    sponsor: SponsorConfig
    truth: TruthConfig
    baseline_risk: BaselineRiskConfig
    sample_size: SampleSizeConfig
    missingness: MissingnessConfig
    engine: EngineConfig


class SuiteOutputsConfig(BaseModel):
    base_dir: str = "outputs/runs"


class SimulationConfig(BaseModel):
    schema_version: str = "1.0"
    seed_master: int = 42
    n_replications: int = Field(default=50, ge=1)
    topics: List[TopicConfig] = Field(min_length=1)
    suite_outputs: SuiteOutputsConfig = Field(default_factory=SuiteOutputsConfig)
