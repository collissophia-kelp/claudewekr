"""Revenue projection engine for Kelp Target Engine."""

from engine.models import Company


def calculate_revenue(company: Company, config: dict) -> float:
    """Calculate Year 5 revenue for a company.

    Formula: hectares * coverage_pct * application_rate * applications_per_season * price_per_litre
    Uses per-company overrides if set, otherwise falls back to global assumptions.
    """
    assumptions = config["revenue_assumptions"]

    coverage = company.override_coverage_pct if company.override_coverage_pct is not None else assumptions["coverage_pct"]
    rate = company.override_application_rate if company.override_application_rate is not None else assumptions["application_rate_litres_per_ha"]
    apps = company.override_applications_per_season if company.override_applications_per_season is not None else assumptions["applications_per_season"]
    price = company.override_price_per_litre if company.override_price_per_litre is not None else assumptions["price_per_litre_eur"]

    return round(company.hectares_controlled * coverage * rate * apps * price, 2)


def revenue_scenario(companies: list[Company], config: dict,
                     overrides: dict[str, float]) -> list[dict]:
    """Model a revenue scenario with modified assumptions.

    overrides can contain: coverage_pct, application_rate_litres_per_ha,
    applications_per_season, price_per_litre_eur

    Returns list of dicts with company_name, current_revenue, scenario_revenue, delta.
    """
    scenario_config = {
        **config,
        "revenue_assumptions": {**config["revenue_assumptions"], **overrides},
    }

    results = []
    for c in companies:
        current = calculate_revenue(c, config)
        scenario = calculate_revenue(c, scenario_config)
        if current > 0 or scenario > 0:
            results.append({
                "company_name": c.company_name,
                "hectares": c.hectares_controlled,
                "current_revenue": current,
                "scenario_revenue": scenario,
                "delta": round(scenario - current, 2),
                "delta_pct": round((scenario - current) / current * 100, 1) if current > 0 else 0,
            })

    results.sort(key=lambda x: -abs(x["delta"]))
    return results
