"""Dashboard and summary endpoints."""

from fastapi import APIRouter

from backend.models.schemas import DashboardSummary, MarketShareData
from backend.services.data_service import get_dashboard_summary, get_market_share

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary():
    """Get full dashboard summary: tier distribution, pipeline funnel, top companies."""
    return get_dashboard_summary()


@router.get("/market-share", response_model=list[MarketShareData])
def market_share():
    """Get market share data by region."""
    return get_market_share()
