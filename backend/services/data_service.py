"""Data service — bridges existing Kelp Target Engine data to the API."""

import json
import sys
from pathlib import Path

# Add parent dir so we can import the existing engine
ENGINE_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ENGINE_ROOT))

from engine.models import Company, load_companies, save_companies, DEFAULT_COMPANIES_PATH
from engine.config import load_config
from engine.scoring import score_company, calculate_weighted_score, assign_tier
from engine.revenue import calculate_revenue
from engine.pipeline import STAGE_ORDER

from backend.models.schemas import (
    CompanySummary, CompanyDetail, CompanyScores,
    DashboardSummary, PipelineFunnel, TierDistribution,
    CropBaseline, FarmerROI, FarmerROIScenario,
    ProjectionYear, BusinessCase, MarketShareData,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def get_config() -> dict:
    return load_config()


def get_companies() -> list[Company]:
    return load_companies(DEFAULT_COMPANIES_PATH)


def _to_summary(c: Company, config: dict) -> CompanySummary:
    ws_val, tier, tier_label = score_company(c, config)
    rev = calculate_revenue(c, config)
    return CompanySummary(
        company_name=c.company_name,
        hq_country=c.hq_country,
        region=c.region,
        business_type=c.business_type,
        main_crops=c.main_crops,
        tier=tier,
        tier_label=tier_label,
        weighted_score=round(ws_val, 2),
        pipeline_stage=c.pipeline_stage,
        pipeline_owner=c.pipeline_owner,
        hectares_controlled=c.hectares_controlled,
        projected_revenue=round(rev, 2),
        tags=c.tags,
        excluded=c.excluded,
    )


def _to_detail(c: Company, config: dict) -> CompanyDetail:
    ws_val, tier, tier_label = score_company(c, config)
    rev = calculate_revenue(c, config)
    return CompanyDetail(
        company_name=c.company_name,
        hq_country=c.hq_country,
        region=c.region,
        business_type=c.business_type,
        countries_with_controlled_farms=c.countries_with_controlled_farms,
        main_crops=c.main_crops,
        tier=tier,
        tier_label=tier_label,
        weighted_score=round(ws_val, 2),
        pipeline_stage=c.pipeline_stage,
        pipeline_owner=c.pipeline_owner,
        hectares_controlled=c.hectares_controlled,
        projected_revenue=round(rev, 2),
        tags=c.tags,
        excluded=c.excluded,
        scores=CompanyScores(
            integration=c.score_integration,
            high_value_crop=c.score_high_value_crop,
            registration_ease=c.score_registration_ease,
            scale_potential=c.score_scale_potential,
            strategic_leverage=c.score_strategic_leverage,
            penalty_complexity=c.penalty_complexity,
        ),
        notes=c.notes,
        exclusion_reason=c.exclusion_reason,
        override_coverage_pct=c.override_coverage_pct,
        override_application_rate=c.override_application_rate,
        override_applications_per_season=c.override_applications_per_season,
        override_price_per_litre=c.override_price_per_litre,
    )


def list_companies(
    region: str | None = None,
    tier: int | None = None,
    stage: str | None = None,
    crop: str | None = None,
    search: str | None = None,
    include_excluded: bool = False,
) -> list[CompanySummary]:
    config = get_config()
    companies = get_companies()

    results = []
    for c in companies:
        if not include_excluded and c.excluded:
            continue
        if region and c.region.lower() != region.lower():
            continue
        if stage and c.pipeline_stage != stage:
            continue
        if crop and not any(crop.lower() in cr.lower() for cr in c.main_crops):
            continue
        if search:
            q = search.lower()
            if not (q in c.company_name.lower() or q in c.hq_country.lower()
                    or q in c.region.lower() or any(q in cr.lower() for cr in c.main_crops)):
                continue

        summary = _to_summary(c, config)
        if tier and summary.tier != tier:
            continue
        results.append(summary)

    results.sort(key=lambda x: -x.weighted_score)
    return results


def get_company_detail(name: str) -> CompanyDetail | None:
    config = get_config()
    companies = get_companies()
    name_lower = name.lower()
    for c in companies:
        if c.company_name.lower() == name_lower:
            return _to_detail(c, config)
    return None


def update_company_scores(name: str, updates: dict) -> CompanyDetail | None:
    config = get_config()
    companies = get_companies()
    name_lower = name.lower()
    for c in companies:
        if c.company_name.lower() == name_lower:
            if "integration" in updates and updates["integration"] is not None:
                c.score_integration = updates["integration"]
            if "high_value_crop" in updates and updates["high_value_crop"] is not None:
                c.score_high_value_crop = updates["high_value_crop"]
            if "registration_ease" in updates and updates["registration_ease"] is not None:
                c.score_registration_ease = updates["registration_ease"]
            if "scale_potential" in updates and updates["scale_potential"] is not None:
                c.score_scale_potential = updates["scale_potential"]
            if "strategic_leverage" in updates and updates["strategic_leverage"] is not None:
                c.score_strategic_leverage = updates["strategic_leverage"]
            if "penalty_complexity" in updates and updates["penalty_complexity"] is not None:
                c.penalty_complexity = updates["penalty_complexity"]
            c.touch()
            save_companies(companies, DEFAULT_COMPANIES_PATH)
            return _to_detail(c, config)
    return None


def get_dashboard_summary() -> DashboardSummary:
    config = get_config()
    companies = get_companies()

    active = [c for c in companies if not c.excluded]
    scored = [(c, *score_company(c, config)) for c in active]
    scored.sort(key=lambda x: -x[1])

    # Pipeline funnel
    stage_names = config.get("pipeline_stages", {})
    funnel = []
    for stage in reversed(STAGE_ORDER):
        stage_cos = [(c, ws) for c, ws, _, _ in scored if c.pipeline_stage == stage]
        ha = sum(c.hectares_controlled for c, _ in stage_cos)
        rev = sum(calculate_revenue(c, config) for c, _ in stage_cos)
        top = [c.company_name for c, _ in sorted(stage_cos, key=lambda x: -calculate_revenue(x[0], config))[:3]]
        funnel.append(PipelineFunnel(
            stage=stage, stage_name=stage_names.get(stage, stage),
            count=len(stage_cos), hectares=ha, revenue=round(rev, 2),
            top_companies=top,
        ))

    # Tier distribution
    tier_counts: dict[int, dict] = {}
    for c, ws_val, tier, tl in scored:
        if tier not in tier_counts:
            tier_counts[tier] = {"label": tl, "count": 0, "revenue": 0.0}
        tier_counts[tier]["count"] += 1
        tier_counts[tier]["revenue"] += calculate_revenue(c, config)

    tiers = [
        TierDistribution(tier=t, label=d["label"], count=d["count"], revenue=round(d["revenue"], 2))
        for t, d in sorted(tier_counts.items())
    ]

    # Top 10 by revenue
    top_companies = [_to_summary(c, config) for c, _, _, _ in scored[:10]]

    return DashboardSummary(
        total_companies=len(companies),
        total_active=len(active),
        total_excluded=len(companies) - len(active),
        total_hectares=sum(c.hectares_controlled for c in active),
        total_projected_revenue=round(sum(calculate_revenue(c, config) for c in active), 2),
        pipeline_funnel=funnel,
        tier_distribution=tiers,
        top_companies=top_companies,
    )


def get_crop_baselines() -> list[CropBaseline]:
    path = DATA_DIR / "crop_baselines.json"
    data = json.loads(path.read_text())
    return [CropBaseline(**item) for item in data["crops"]]


def get_market_data() -> dict:
    path = DATA_DIR / "market_data.json"
    return json.loads(path.read_text())


def calculate_farmer_roi(
    crop: str, country: str, area_ha: float = 100.0,
    uplifts: list[float] | None = None,
) -> FarmerROI:
    if uplifts is None:
        uplifts = [5.0, 10.0, 15.0]

    baselines = get_crop_baselines()
    baseline = None
    for b in baselines:
        if b.crop.lower() == crop.lower() and b.country.lower() == country.lower():
            baseline = b
            break

    if not baseline:
        # Fallback: use generic values
        baseline = CropBaseline(
            crop=crop, country=country, currency="USD",
            yield_per_ha=5.0, price_per_tonne=500, cost_per_ha=2000,
            stimblue_cost_per_ha=45,
        )

    scenarios = []
    break_even = 0.0

    for uplift_pct in uplifts:
        base_yield = baseline.yield_per_ha * area_ha
        new_yield = base_yield * (1 + uplift_pct / 100)
        base_rev = base_yield * baseline.price_per_tonne
        new_rev = new_yield * baseline.price_per_tonne
        uplift_rev = new_rev - base_rev
        stimblue_cost = baseline.stimblue_cost_per_ha * area_ha
        net = uplift_rev - stimblue_cost
        roi = (net / stimblue_cost * 100) if stimblue_cost > 0 else 0

        scenarios.append(FarmerROIScenario(
            uplift_pct=uplift_pct,
            baseline_yield=round(base_yield, 1),
            new_yield=round(new_yield, 1),
            baseline_revenue=round(base_rev, 2),
            new_revenue=round(new_rev, 2),
            uplift_revenue=round(uplift_rev, 2),
            stimblue_cost=round(stimblue_cost, 2),
            net_benefit=round(net, 2),
            roi_pct=round(roi, 1),
            currency=baseline.currency,
        ))

    # Calculate break-even uplift %
    stimblue_total = baseline.stimblue_cost_per_ha * area_ha
    base_rev = baseline.yield_per_ha * area_ha * baseline.price_per_tonne
    if base_rev > 0:
        break_even = (stimblue_total / base_rev) * 100

    return FarmerROI(
        crop=crop, country=country, area_ha=area_ha,
        scenarios=scenarios, break_even_uplift_pct=round(break_even, 2),
    )


def build_projections(
    company_name: str,
    hectares: float | None = None,
    ramp_years: int = 3,
) -> list[ProjectionYear]:
    config = get_config()
    assumptions = config["revenue_assumptions"]

    companies = get_companies()
    company = None
    for c in companies:
        if c.company_name.lower() == company_name.lower():
            company = c
            break

    ha = hectares or (company.hectares_controlled if company else 10000)

    projections = []
    for year in range(1, 11):
        # Ramp: year 1 = 20%, year 2 = 50%, year 3+ = 80% (or configured)
        if year == 1:
            cov = 0.20
        elif year == 2:
            cov = 0.50
        elif year <= ramp_years:
            cov = 0.65
        else:
            cov = assumptions["coverage_pct"]

        treated = ha * cov
        rate = assumptions["application_rate_litres_per_ha"]
        apps = assumptions["applications_per_season"]
        price = assumptions["price_per_litre_eur"]

        litres = treated * rate * apps
        rev_eur = litres * price

        projections.append(ProjectionYear(
            year=year, hectares=ha, coverage_pct=round(cov, 2),
            treated_hectares=round(treated, 0),
            litres_required=round(litres, 0),
            revenue_eur=round(rev_eur, 2),
        ))

    return projections


def get_market_share() -> list[MarketShareData]:
    market = get_market_data()
    config = get_config()
    companies = get_companies()
    active = [c for c in companies if not c.excluded]

    # Sum hectares per region from our pipeline
    region_ha: dict[str, float] = {}
    for c in active:
        r = c.region or "Unknown"
        region_ha[r] = region_ha.get(r, 0) + c.hectares_controlled

    results = []
    for region_data in market.get("regions", []):
        r = region_data["region"]
        total_ha = region_data["total_arable_hectares_m"] * 1_000_000
        biostim_ha = region_data["biostimulant_hectares_m"] * 1_000_000
        our_ha = region_ha.get(r, 0)
        untapped = biostim_ha - our_ha

        results.append(MarketShareData(
            region=r,
            total_addressable_hectares=total_ha,
            current_biostim_hectares=biostim_ha,
            stimblue_hectares=our_ha,
            untapped_hectares=max(0, untapped),
            penetration_pct=round((our_ha / biostim_ha * 100) if biostim_ha > 0 else 0, 2),
        ))

    return results


def update_scoring_config(updates: dict) -> dict:
    """Update scoring weights and/or tier thresholds and persist."""
    from engine.config import save_config
    config = get_config()

    if "scoring_weights" in updates:
        config["scoring_weights"].update(updates["scoring_weights"])
    if "tier_thresholds" in updates:
        config["tier_thresholds"].update(updates["tier_thresholds"])
    if "revenue_assumptions" in updates:
        config["revenue_assumptions"].update(updates["revenue_assumptions"])

    save_config(config)
    return config


def what_if_scoring(weight_overrides: dict) -> list[CompanySummary]:
    """Simulate score changes with different weights. Does NOT persist."""
    config = get_config()
    sim_config = json.loads(json.dumps(config))
    sim_config["scoring_weights"].update(weight_overrides)

    companies = get_companies()
    active = [c for c in companies if not c.excluded]

    results = []
    for c in active:
        ws_val, tier, tier_label = score_company(c, sim_config)
        rev = calculate_revenue(c, sim_config)
        results.append(CompanySummary(
            company_name=c.company_name,
            hq_country=c.hq_country,
            region=c.region,
            business_type=c.business_type,
            main_crops=c.main_crops,
            tier=tier,
            tier_label=tier_label,
            weighted_score=round(ws_val, 2),
            pipeline_stage=c.pipeline_stage,
            pipeline_owner=c.pipeline_owner,
            hectares_controlled=c.hectares_controlled,
            projected_revenue=round(rev, 2),
            tags=c.tags,
            excluded=c.excluded,
        ))

    results.sort(key=lambda x: -x.weighted_score)
    return results


def create_company(data: dict) -> CompanyDetail:
    """Create a new company and persist."""
    config = get_config()
    companies = get_companies()

    c = Company(
        company_name=data["company_name"],
        hq_country=data.get("hq_country", ""),
        region=data.get("region", ""),
        business_type=data.get("business_type", ""),
        countries_with_controlled_farms=data.get("countries_with_controlled_farms", ""),
        main_crops=data.get("main_crops", []),
        score_integration=data.get("score_integration", 0),
        score_high_value_crop=data.get("score_high_value_crop", 0),
        score_registration_ease=data.get("score_registration_ease", 0),
        score_scale_potential=data.get("score_scale_potential", 0),
        score_strategic_leverage=data.get("score_strategic_leverage", 0),
        penalty_complexity=data.get("penalty_complexity", 0),
        pipeline_stage=data.get("pipeline_stage", "L1"),
        pipeline_owner=data.get("pipeline_owner", ""),
        hectares_controlled=data.get("hectares_controlled", 0),
        notes=data.get("notes", ""),
    )

    companies.append(c)
    save_companies(companies, DEFAULT_COMPANIES_PATH)
    return _to_detail(c, config)


def get_currency_rate(from_currency: str, to_currency: str) -> dict:
    """Get exchange rate between two currencies."""
    market = get_market_data()
    rates = market.get("exchange_rates_to_eur", {})

    from_upper = from_currency.upper()
    to_upper = to_currency.upper()

    from_to_eur = rates.get(from_upper, 1.0)
    to_to_eur = rates.get(to_upper, 1.0)

    if to_to_eur == 0:
        rate = 0
    else:
        rate = from_to_eur / to_to_eur

    return {
        "from": from_upper,
        "to": to_upper,
        "rate": round(rate, 6),
        "inverse": round(1 / rate, 6) if rate > 0 else 0,
    }
