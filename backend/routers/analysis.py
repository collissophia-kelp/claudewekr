"""Analysis endpoints: farmer ROI, projections, company analysis."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from backend.models.schemas import FarmerROI, ProjectionYear
from backend.services.data_service import calculate_farmer_roi, build_projections, create_company

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class AnalyseRequest(BaseModel):
    url: str


@router.post("/analyse")
async def analyse_company(request: AnalyseRequest):
    """Submit a company URL for AI-powered analysis via Claude API."""
    from backend.services.claude_analyser import analyse_company as _analyse
    result = await _analyse(request.url)

    if "error" in result:
        return result

    # Auto-save as a new company if analysis succeeded
    scores = result.get("matrix_scores", {})
    company_data = {
        "company_name": result.get("company_name", "Unknown"),
        "hq_country": result.get("hq_country", ""),
        "region": ", ".join(result.get("regions", [])),
        "business_type": result.get("business_type", ""),
        "countries_with_controlled_farms": ", ".join(result.get("countries_with_farms", [])),
        "main_crops": [c["crop"] for c in result.get("main_crops", [])],
        "score_integration": scores.get("integration", 0),
        "score_high_value_crop": scores.get("high_value_crop", 0),
        "score_registration_ease": scores.get("registration_ease", 0),
        "score_scale_potential": scores.get("scale_potential", 0),
        "score_strategic_leverage": scores.get("strategic_leverage", 0),
        "penalty_complexity": scores.get("penalty_complexity", 0),
        "hectares_controlled": result.get("total_hectares_controlled", 0),
        "pipeline_stage": "L1",
        "notes": f"AI-analysed from {request.url}",
    }

    try:
        company_detail = create_company(company_data)
        result["_saved"] = True
        result["_company_name"] = company_detail.company_name
        result["_tier"] = company_detail.tier
        result["_weighted_score"] = company_detail.weighted_score
    except Exception as e:
        result["_saved"] = False
        result["_save_error"] = str(e)

    return result


@router.get("/farmer-roi", response_model=FarmerROI)
def farmer_roi(
    crop: str = Query(..., description="Crop name"),
    country: str = Query(..., description="Country name"),
    area_ha: float = Query(100.0, description="Farm area in hectares"),
):
    """Calculate farmer ROI for Stimblue+ on a given crop/country/area."""
    return calculate_farmer_roi(crop=crop, country=country, area_ha=area_ha)


@router.get("/projections/{company_name}", response_model=list[ProjectionYear])
def projections(
    company_name: str,
    hectares: float | None = Query(None, description="Override hectares"),
    ramp_years: int = Query(3, ge=1, le=5, description="Years to full ramp"),
):
    """Get 10-year revenue projection for a company."""
    return build_projections(
        company_name=company_name, hectares=hectares, ramp_years=ramp_years,
    )
