"""Company API endpoints."""

from fastapi import APIRouter, HTTPException, Query

from backend.models.schemas import CompanySummary, CompanyDetail, ScoreUpdate
from backend.services.data_service import list_companies, get_company_detail, update_company_scores

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("", response_model=list[CompanySummary])
def get_companies(
    region: str | None = Query(None),
    tier: int | None = Query(None, ge=1, le=4),
    stage: str | None = Query(None),
    crop: str | None = Query(None),
    search: str | None = Query(None),
    include_excluded: bool = Query(False),
):
    """List companies with optional filters."""
    return list_companies(
        region=region, tier=tier, stage=stage, crop=crop,
        search=search, include_excluded=include_excluded,
    )


@router.get("/{company_name}", response_model=CompanyDetail)
def get_company(company_name: str):
    """Get full detail for a single company."""
    detail = get_company_detail(company_name)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Company '{company_name}' not found")
    return detail


@router.patch("/{company_name}/scores", response_model=CompanyDetail)
def patch_scores(company_name: str, updates: ScoreUpdate):
    """Update scores for a company. Only provided fields are updated."""
    result = update_company_scores(company_name, updates.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail=f"Company '{company_name}' not found")
    return result
