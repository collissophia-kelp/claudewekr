"""Config and scoring endpoints."""

from fastapi import APIRouter

from backend.models.schemas import ScoringConfig, CropBaseline, CompanySummary
from backend.services.data_service import (
    get_config, get_crop_baselines, get_market_data,
    update_scoring_config, what_if_scoring, get_currency_rate,
)

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


@router.put("/scoring")
def update_scoring(updates: dict):
    """Update scoring weights, tier thresholds, or revenue assumptions. Persists to config.json."""
    config = update_scoring_config(updates)
    return ScoringConfig(
        scoring_weights=config.get("scoring_weights", {}),
        tier_thresholds=config.get("tier_thresholds", {}),
        revenue_assumptions=config.get("revenue_assumptions", {}),
    )


@router.post("/what-if", response_model=list[CompanySummary])
def what_if(weight_overrides: dict):
    """Simulate scoring with different weights. Does NOT persist changes."""
    return what_if_scoring(weight_overrides)


@router.get("/crop-baselines", response_model=list[CropBaseline])
def crop_baselines():
    """Get all crop baseline data."""
    return get_crop_baselines()


@router.get("/market-data")
def market_data():
    """Get biostimulant market data by region."""
    return get_market_data()


@router.get("/currency/{from_currency}/{to_currency}")
def currency_rate(from_currency: str, to_currency: str):
    """Get exchange rate between two currencies."""
    return get_currency_rate(from_currency, to_currency)
