"""Tests for the revenue projection engine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.models import Company
from engine.revenue import calculate_revenue, revenue_scenario

DEFAULT_CONFIG = {
    "scoring_weights": {
        "integration": 0.35, "high_value_crop": 0.25,
        "registration_ease": 0.20, "scale_potential": 0.15,
        "strategic_leverage": 0.05, "penalty_complexity": -0.10,
    },
    "tier_thresholds": {"tier_1_min": 4.0, "tier_2_min": 3.2, "tier_3_min": 2.5},
    "revenue_assumptions": {
        "coverage_pct": 0.80,
        "application_rate_litres_per_ha": 2,
        "applications_per_season": 3,
        "price_per_litre_eur": 7.50,
    },
}


def _make_company(**kwargs):
    defaults = {"company_name": "Test Co", "hectares_controlled": 50000}
    defaults.update(kwargs)
    return Company(**defaults)


class TestRevenueCalculation:
    def test_spec_example(self):
        """50,000 ha * 0.80 * 2 * 3 * 7.50 = 1,800,000."""
        c = _make_company(hectares_controlled=50000)
        rev = calculate_revenue(c, DEFAULT_CONFIG)
        assert rev == 1_800_000.0

    def test_zero_hectares(self):
        c = _make_company(hectares_controlled=0)
        rev = calculate_revenue(c, DEFAULT_CONFIG)
        assert rev == 0.0

    def test_hortifrut_example(self):
        """15,000 ha * 0.80 * 2 * 3 * 7.50 = 540,000."""
        c = _make_company(hectares_controlled=15000)
        rev = calculate_revenue(c, DEFAULT_CONFIG)
        assert rev == 540_000.0

    def test_per_company_override(self):
        """Company with override should use override values."""
        c = _make_company(
            hectares_controlled=10000,
            override_price_per_litre=10.0,
        )
        rev = calculate_revenue(c, DEFAULT_CONFIG)
        # 10000 * 0.80 * 2 * 3 * 10.0 = 480,000
        assert rev == 480_000.0

    def test_all_overrides(self):
        c = _make_company(
            hectares_controlled=10000,
            override_coverage_pct=1.0,
            override_application_rate=3.0,
            override_applications_per_season=4,
            override_price_per_litre=10.0,
        )
        rev = calculate_revenue(c, DEFAULT_CONFIG)
        # 10000 * 1.0 * 3.0 * 4 * 10.0 = 1,200,000
        assert rev == 1_200_000.0


class TestRevenueScenario:
    def test_price_increase(self):
        c = _make_company(hectares_controlled=10000)
        results = revenue_scenario(
            [c], DEFAULT_CONFIG,
            {"price_per_litre_eur": 10.0},
        )
        assert len(results) == 1
        # Current: 10000 * 0.80 * 2 * 3 * 7.50 = 360,000
        # Scenario: 10000 * 0.80 * 2 * 3 * 10.0 = 480,000
        assert results[0]["current_revenue"] == 360_000.0
        assert results[0]["scenario_revenue"] == 480_000.0
        assert results[0]["delta"] == 120_000.0
