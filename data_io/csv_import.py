"""Bulk import companies from CSV files."""

import csv
from pathlib import Path

from engine.models import Company
from engine.tags import auto_generate_tags


def import_csv(file_path: str) -> tuple[list[Company], list[str]]:
    """Import companies from a CSV file.

    Expected columns (flexible header matching):
      company_name, hq_country, region, business_type,
      countries_with_controlled_farms, main_crops,
      score_integration, score_high_value_crop, score_registration_ease,
      score_scale_potential, score_strategic_leverage, penalty_complexity,
      hectares_controlled, pipeline_stage, pipeline_owner, notes

    Returns (companies, warnings).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    warnings = []
    companies = []

    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            warnings.append("CSV file has no headers")
            return companies, warnings

        # Normalise headers
        field_map = _build_csv_field_map(reader.fieldnames)

        for row_num, row in enumerate(reader, start=2):
            name = _get_field(row, field_map, "company_name")
            if not name or not name.strip():
                continue

            try:
                company = Company(
                    company_name=name.strip(),
                    hq_country=_get_field(row, field_map, "hq_country") or "",
                    region=_get_field(row, field_map, "region") or "",
                    business_type=_get_field(row, field_map, "business_type") or "",
                    countries_with_controlled_farms=_get_field(row, field_map, "countries") or "",
                    main_crops=_parse_list(_get_field(row, field_map, "main_crops")),
                    score_integration=_safe_float(_get_field(row, field_map, "integration")),
                    score_high_value_crop=_safe_float(_get_field(row, field_map, "high_value_crop")),
                    score_registration_ease=_safe_float(_get_field(row, field_map, "registration_ease")),
                    score_scale_potential=_safe_float(_get_field(row, field_map, "scale_potential")),
                    score_strategic_leverage=_safe_float(_get_field(row, field_map, "strategic_leverage")),
                    penalty_complexity=_safe_float(_get_field(row, field_map, "penalty_complexity")),
                    hectares_controlled=_safe_float(_get_field(row, field_map, "hectares")),
                    pipeline_stage=_get_field(row, field_map, "pipeline_stage") or "L0",
                    pipeline_owner=_get_field(row, field_map, "owner") or "",
                    notes=_get_field(row, field_map, "notes") or "",
                )
                company.tags = auto_generate_tags(company)
                companies.append(company)
            except Exception as e:
                warnings.append(f"Row {row_num}: Error parsing '{name}': {e}")

    return companies, warnings


def _build_csv_field_map(fieldnames: list[str]) -> dict[str, str | None]:
    """Map our internal field names to CSV column headers."""
    normalised = {f.strip().lower().replace(" ", "_"): f for f in fieldnames}

    aliases = {
        "company_name": ["company_name", "company", "name"],
        "hq_country": ["hq_country", "country", "headquarters"],
        "region": ["region"],
        "business_type": ["business_type", "type", "business_description"],
        "countries": ["countries_with_controlled_farms", "countries", "farm_countries"],
        "main_crops": ["main_crops", "crops", "main_crops_(top_5)"],
        "integration": ["score_integration", "integration", "vertical_integration"],
        "high_value_crop": ["score_high_value_crop", "high_value_crop", "high-value_crop"],
        "registration_ease": ["score_registration_ease", "registration_ease", "registration"],
        "scale_potential": ["score_scale_potential", "scale_potential", "scale"],
        "strategic_leverage": ["score_strategic_leverage", "strategic_leverage", "leverage"],
        "penalty_complexity": ["penalty_complexity", "penalty", "complexity_penalty"],
        "hectares": ["hectares_controlled", "hectares", "ha"],
        "pipeline_stage": ["pipeline_stage", "stage", "pipeline"],
        "owner": ["pipeline_owner", "owner", "assigned_to"],
        "notes": ["notes", "comments", "evidence"],
    }

    field_map = {}
    for field, possible in aliases.items():
        field_map[field] = None
        for alias in possible:
            if alias in normalised:
                field_map[field] = normalised[alias]
                break

    return field_map


def _get_field(row: dict, field_map: dict, field: str) -> str | None:
    """Get a field value from a CSV row using the field map."""
    col_name = field_map.get(field)
    if col_name is None:
        return None
    return row.get(col_name, "").strip() or None


def _safe_float(value: str | None) -> float:
    """Parse string to float, returning 0.0 on failure."""
    if not value:
        return 0.0
    try:
        return float(value.replace(",", ""))
    except (ValueError, TypeError):
        return 0.0


def _parse_list(value: str | None) -> list[str]:
    """Parse comma-separated string to list."""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]
