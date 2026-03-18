"""Config and scoring endpoints."""

from fastapi import APIRouter

from backend.models.schemas import ScoringConfig, CropBaseline
from backend.services.data_service import get_config, get_crop_baselines, get_market_data

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/scoring", response_model=ScoringConfig)
def scoring_config():
    """Get current scoring weights, tier thresholds, and revenue assumptions."""
    config = get_config()
    return ScoringConfig(
        scoring_weights=config.get("scoring_weights", {}),
        tier_thresholds=config.get("tier_thresholds", {}),
        revenue_assumptions=config.get("revenue_assumptions", {}),
    )


@router.get("/crop-baselines", response_model=list[CropBaseline])
def crop_baselines():
    """Get all crop baseline data."""
    return get_crop_baselines()


@router.get("/market-data")
def market_data():
    """Get biostimulant market data by region."""
    return get_market_data()
