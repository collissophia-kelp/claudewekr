"""Pydantic models for the Stimblue+ Dashboard API."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Company Models (mirrors engine/models.py for API layer) ──────────


class CompanyScores(BaseModel):
    integration: float = 0.0
    high_value_crop: float = 0.0
    registration_ease: float = 0.0
    scale_potential: float = 0.0
    strategic_leverage: float = 0.0
    penalty_complexity: float = 0.0


class CompanySummary(BaseModel):
    """Lightweight company record for list views."""
    company_name: str
    hq_country: str = ""
    region: str = ""
    business_type: str = ""
    main_crops: list[str] = []
    tier: int = 4
    tier_label: str = "Tier 4"
    weighted_score: float = 0.0
    pipeline_stage: str = "L0"
    pipeline_owner: str = ""
    hectares_controlled: float = 0.0
    projected_revenue: float = 0.0
    tags: list[str] = []
    excluded: bool = False


class CompanyDetail(CompanySummary):
    """Full company record for detail views."""
    countries_with_controlled_farms: str = ""
    scores: CompanyScores = Field(default_factory=CompanyScores)
    notes: str = ""
    exclusion_reason: str = ""
    override_coverage_pct: float | None = None
    override_application_rate: float | None = None
    override_applications_per_season: int | None = None
    override_price_per_litre: float | None = None


class ScoreUpdate(BaseModel):
    """Request body for updating a single company's scores."""
    integration: float | None = None
    high_value_crop: float | None = None
    registration_ease: float | None = None
    scale_potential: float | None = None
    strategic_leverage: float | None = None
    penalty_complexity: float | None = None


# ── Scoring Config ───────────────────────────────────────────────────


class ScoringWeights(BaseModel):
    integration: float = 0.35
    high_value_crop: float = 0.20
    registration_ease: float = 0.10
    scale_potential: float = 0.30
    strategic_leverage: float = 0.05
    penalty_complexity: float = -0.10


class TierThresholds(BaseModel):
    tier_1_min: float = 4.0
    tier_2_min: float = 3.2
    tier_3_min: float = 2.5


class RevenueAssumptions(BaseModel):
    coverage_pct: float = 0.80
    application_rate_litres_per_ha: float = 2.0
    applications_per_season: int = 3
    price_per_litre_eur: float = 7.50


class ScoringConfig(BaseModel):
    scoring_weights: ScoringWeights = Field(default_factory=ScoringWeights)
    tier_thresholds: TierThresholds = Field(default_factory=TierThresholds)
    revenue_assumptions: RevenueAssumptions = Field(default_factory=RevenueAssumptions)


# ── Business Case / Projections ──────────────────────────────────────


class CropBaseline(BaseModel):
    """Baseline yield and revenue data for a crop in a country."""
    crop: str
    country: str
    currency: str = "USD"
    yield_per_ha: float = 0.0  # tonnes/ha
    price_per_tonne: float = 0.0  # local currency
    cost_per_ha: float = 0.0  # local currency
    stimblue_cost_per_ha: float = 45.0  # EUR


class ProjectionYear(BaseModel):
    """One year of a 10-year projection."""
    year: int
    hectares: float = 0.0
    coverage_pct: float = 0.0
    treated_hectares: float = 0.0
    litres_required: float = 0.0
    revenue_eur: float = 0.0
    revenue_local: float = 0.0
    currency: str = "EUR"


class BusinessCase(BaseModel):
    """Business case for a single company."""
    company_name: str
    region: str = ""
    crops: list[CropBaseline] = []
    projections: list[ProjectionYear] = []
    total_10yr_revenue_eur: float = 0.0
    npv_eur: float = 0.0


# ── Farmer ROI ───────────────────────────────────────────────────────


class FarmerROIScenario(BaseModel):
    """ROI scenario for a specific uplift percentage."""
    uplift_pct: float  # 5, 10, 15
    baseline_yield: float = 0.0
    new_yield: float = 0.0
    baseline_revenue: float = 0.0
    new_revenue: float = 0.0
    uplift_revenue: float = 0.0
    stimblue_cost: float = 0.0
    net_benefit: float = 0.0
    roi_pct: float = 0.0
    currency: str = "USD"


class FarmerROI(BaseModel):
    """Complete farmer ROI analysis."""
    crop: str
    country: str
    area_ha: float = 100.0
    scenarios: list[FarmerROIScenario] = []
    break_even_uplift_pct: float = 0.0


# ── Dashboard Summary ────────────────────────────────────────────────


class PipelineFunnel(BaseModel):
    stage: str
    stage_name: str
    count: int = 0
    hectares: float = 0.0
    revenue: float = 0.0
    top_companies: list[str] = []


class TierDistribution(BaseModel):
    tier: int
    label: str
    count: int = 0
    revenue: float = 0.0


class DashboardSummary(BaseModel):
    total_companies: int = 0
    total_active: int = 0
    total_excluded: int = 0
    total_hectares: float = 0.0
    total_projected_revenue: float = 0.0
    pipeline_funnel: list[PipelineFunnel] = []
    tier_distribution: list[TierDistribution] = []
    top_companies: list[CompanySummary] = []


# ── Market Share ─────────────────────────────────────────────────────


class MarketShareData(BaseModel):
    region: str
    total_addressable_hectares: float = 0.0
    current_biostim_hectares: float = 0.0
    stimblue_hectares: float = 0.0
    untapped_hectares: float = 0.0
    penetration_pct: float = 0.0
