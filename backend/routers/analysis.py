"""Analysis endpoints: farmer ROI, projections, business case."""

from fastapi import APIRouter, Query

from backend.models.schemas import FarmerROI, ProjectionYear
from backend.services.data_service import calculate_farmer_roi, build_projections

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


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
