"""Scoring engine: weighted score calculation, tier assignment, what-if analysis."""

from engine.models import Company


def calculate_weighted_score(company: Company, weights: dict[str, float]) -> float:
    """Calculate the weighted score for a company using the given weights."""
    scores = company.get_scores_dict()
    total = 0.0
    for key, weight in weights.items():
        total += scores.get(key, 0.0) * weight
    return round(total, 2)


def assign_tier(weighted_score: float, thresholds: dict[str, float]) -> int:
    """Assign a tier (1-4) based on weighted score and thresholds."""
    if weighted_score >= thresholds["tier_1_min"]:
        return 1
    elif weighted_score >= thresholds["tier_2_min"]:
        return 2
    elif weighted_score >= thresholds["tier_3_min"]:
        return 3
    else:
        return 4


def tier_label(tier: int) -> str:
    """Return a human-readable tier label."""
    return f"Tier {tier}"


def score_company(company: Company, config: dict) -> tuple[float, int, str]:
    """Calculate weighted score, tier, and tier label for a company."""
    weights = config["scoring_weights"]
    thresholds = config["tier_thresholds"]
    ws = calculate_weighted_score(company, weights)
    t = assign_tier(ws, thresholds)
    return ws, t, tier_label(t)


def score_all(companies: list[Company], config: dict) -> list[tuple[Company, float, int, str]]:
    """Score all companies. Returns list of (company, weighted_score, tier, tier_label)."""
    return [(c, *score_company(c, config)) for c in companies]


def what_if(companies: list[Company], config: dict,
            weight_overrides: dict[str, float]) -> list[dict]:
    """Simulate weight changes and return companies whose tiers change.

    Returns a list of dicts with:
      company_name, old_score, new_score, old_tier, new_tier, direction
    """
    current_weights = config["scoring_weights"]
    thresholds = config["tier_thresholds"]

    new_weights = {**current_weights, **weight_overrides}

    changes = []
    for c in companies:
        old_score = calculate_weighted_score(c, current_weights)
        new_score = calculate_weighted_score(c, new_weights)
        old_tier = assign_tier(old_score, thresholds)
        new_tier = assign_tier(new_score, thresholds)

        if old_tier != new_tier:
            direction = "up" if new_tier < old_tier else "down"
            changes.append({
                "company_name": c.company_name,
                "old_score": old_score,
                "new_score": new_score,
                "old_tier": old_tier,
                "new_tier": new_tier,
                "direction": direction,
            })

    changes.sort(key=lambda x: (x["direction"], -abs(x["old_score"] - x["new_score"])))
    return changes


def audit_companies(companies: list[Company]) -> list[dict]:
    """Flag companies with missing or suspicious data."""
    issues = []
    score_fields = [
        "score_integration", "score_high_value_crop", "score_registration_ease",
        "score_scale_potential", "score_strategic_leverage",
    ]
    for c in companies:
        company_issues = []
        # Check for all-zero scores
        scores = [getattr(c, f) for f in score_fields]
        if all(s == 0 for s in scores):
            company_issues.append("All scores are zero")
        # Check for missing region
        if not c.region:
            company_issues.append("Missing region")
        # Check for missing business type
        if not c.business_type:
            company_issues.append("Missing business type")
        # Check for missing crops
        if not c.main_crops:
            company_issues.append("Missing main crops")
        # Check for missing hectares on pipeline companies
        if c.pipeline_stage != "L0" and c.hectares_controlled == 0:
            company_issues.append("In pipeline but hectares = 0")
        # Check for missing HQ country
        if not c.hq_country:
            company_issues.append("Missing HQ country")

        if company_issues:
            issues.append({
                "company_name": c.company_name,
                "issues": company_issues,
            })

    return issues
