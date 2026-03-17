"""Tests for import functionality."""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.models import Company, load_companies, save_companies
from engine.tags import auto_generate_tags
from data_io.csv_import import import_csv


class TestAutoTags:
    def test_generates_crop_tags(self):
        c = Company(
            company_name="Test",
            main_crops=["Banana", "Avocado"],
            region="Latin America",
        )
        tags = auto_generate_tags(c)
        assert "crop:banana" in tags
        assert "crop:avocado" in tags

    def test_generates_region_tag(self):
        c = Company(company_name="Test", region="Western Europe")
        tags = auto_generate_tags(c)
        assert "region:western_europe" in tags

    def test_generates_exclusion_tag(self):
        c = Company(company_name="Test", business_type="Animal feed processor")
        tags = auto_generate_tags(c)
        assert "exclude:animal_feed" in tags

    def test_preserves_existing_tags(self):
        c = Company(
            company_name="Test",
            tags=["strategic:market_opener"],
            region="North America",
        )
        tags = auto_generate_tags(c)
        assert "strategic:market_opener" in tags
        assert "region:north_america" in tags


class TestCsvImport:
    def test_basic_import(self):
        csv_content = (
            "company_name,hq_country,region,score_integration,score_high_value_crop,"
            "score_registration_ease,score_scale_potential,score_strategic_leverage,"
            "penalty_complexity,hectares_controlled\n"
            "Dole,Ireland,Western Europe,5,4,4,5,5,0,100000\n"
            "Chiquita,Switzerland,Western Europe,4,4,4,3,4,-1,50000\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            path = f.name

        try:
            companies, warnings = import_csv(path)
            assert len(companies) == 2
            assert companies[0].company_name == "Dole"
            assert companies[0].score_integration == 5.0
            assert companies[0].hectares_controlled == 100000.0
            assert companies[1].company_name == "Chiquita"
            assert companies[1].penalty_complexity == -1.0
            assert len(warnings) == 0
        finally:
            os.unlink(path)


class TestCompanyPersistence:
    def test_save_and_load(self):
        companies = [
            Company(company_name="Test1", region="Western Europe", score_integration=5),
            Company(company_name="Test2", region="Latin America", score_integration=3),
        ]

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            save_companies(companies, path)
            loaded = load_companies(path)
            assert len(loaded) == 2
            assert loaded[0].company_name == "Test1"
            assert loaded[1].company_name == "Test2"
            assert loaded[0].score_integration == 5.0
        finally:
            os.unlink(path)
