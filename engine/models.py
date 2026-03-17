"""Company data model for Kelp Target Engine."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class PipelineEvent(BaseModel):
    """A pipeline stage transition event."""
    stage: str
    date: str  # ISO format date string
    note: str = ""


class Company(BaseModel):
    """A strategic target company record."""

    # Identification
    company_name: str
    hq_country: str = ""
    region: str = ""
    business_type: str = ""
    countries_with_controlled_farms: str = ""
    main_crops: list[str] = Field(default_factory=list)

    # Scoring (raw inputs only — weighted_score and tier are computed)
    score_integration: float = 0.0
    score_high_value_crop: float = 0.0
    score_registration_ease: float = 0.0
    score_scale_potential: float = 0.0
    score_strategic_leverage: float = 0.0
    penalty_complexity: float = 0.0

    # Pipeline
    pipeline_stage: str = "L0"
    pipeline_owner: str = ""
    pipeline_history: list[PipelineEvent] = Field(default_factory=list)

    # Revenue
    hectares_controlled: float = 0.0

    # Revenue overrides (per-company; None means use global defaults)
    override_coverage_pct: float | None = None
    override_application_rate: float | None = None
    override_applications_per_season: int | None = None
    override_price_per_litre: float | None = None

    # Metadata
    notes: str = ""
    tags: list[str] = Field(default_factory=list)
    date_added: str = Field(default_factory=lambda: date.today().isoformat())
    date_last_updated: str = Field(default_factory=lambda: date.today().isoformat())
    excluded: bool = False
    exclusion_reason: str = ""

    @field_validator("penalty_complexity")
    @classmethod
    def validate_penalty(cls, v: float) -> float:
        if v > 0:
            raise ValueError("penalty_complexity must be 0 or negative (0, -1, or -2)")
        if v < -2:
            raise ValueError("penalty_complexity must be between 0 and -2")
        return v

    def get_scores_dict(self) -> dict[str, float]:
        """Return raw scores as a dict keyed by weight names."""
        return {
            "integration": self.score_integration,
            "high_value_crop": self.score_high_value_crop,
            "registration_ease": self.score_registration_ease,
            "scale_potential": self.score_scale_potential,
            "strategic_leverage": self.score_strategic_leverage,
            "penalty_complexity": self.penalty_complexity,
        }

    def touch(self) -> None:
        """Update the last-updated timestamp."""
        self.date_last_updated = date.today().isoformat()


def load_companies(path) -> list[Company]:
    """Load companies from a JSON file."""
    import json
    from pathlib import Path

    p = Path(path)
    if not p.exists():
        return []
    with open(p, "r") as f:
        data = json.load(f)
    return [Company(**record) for record in data]


def save_companies(companies: list[Company], path) -> None:
    """Save companies to a JSON file."""
    import json
    from pathlib import Path

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump([c.model_dump() for c in companies], f, indent=2, default=str)


DEFAULT_COMPANIES_PATH = __import__("pathlib").Path(__file__).parent.parent / "data" / "companies.json"
