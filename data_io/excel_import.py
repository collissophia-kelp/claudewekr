"""Import companies from existing Strategic Decision Matrix Excel workbook."""

from pathlib import Path

from openpyxl import load_workbook

from engine.models import Company
from engine.tags import auto_generate_tags


def import_xlsx(file_path: str, config: dict) -> tuple[list[Company], list[str]]:
    """Import companies from the Strategic Decision Matrix Excel file.

    Returns (companies, warnings).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    wb = load_workbook(path, data_only=True)
    warnings = []

    # Import from Decision Matrix tab
    companies_dict: dict[str, Company] = {}
    matrix_sheet = _find_sheet(wb, ["Decision Matrix", "DecisionMatrix", "Matrix"])
    if matrix_sheet:
        companies_dict, matrix_warnings = _import_decision_matrix(matrix_sheet, config)
        warnings.extend(matrix_warnings)
    else:
        warnings.append("No 'Decision Matrix' tab found in workbook")

    # Import pipeline data from Target List tab
    target_sheet = _find_sheet(wb, ["Target List", "TargetList", "Targets"])
    if target_sheet:
        target_warnings = _import_target_list(target_sheet, companies_dict, config)
        warnings.extend(target_warnings)
    else:
        warnings.append("No 'Target List' tab found in workbook")

    # Import assumptions if present
    assumptions_sheet = _find_sheet(wb, ["Assumptions"])
    if assumptions_sheet:
        _import_assumptions(assumptions_sheet, config)

    # Auto-generate tags for all companies
    for company in companies_dict.values():
        company.tags = auto_generate_tags(company)

    wb.close()
    return list(companies_dict.values()), warnings


def _find_sheet(wb, names: list[str]):
    """Find a sheet by trying multiple name variants."""
    for name in names:
        if name in wb.sheetnames:
            return wb[name]
    # Try case-insensitive match
    lower_names = [n.lower() for n in names]
    for sheet_name in wb.sheetnames:
        if sheet_name.lower() in lower_names:
            return wb[sheet_name]
    return None


def _import_decision_matrix(sheet, config: dict) -> tuple[dict[str, Company], list[str]]:
    """Parse the Decision Matrix tab.

    Expects header row at row 4 (configurable). Maps columns by header text.
    """
    warnings = []
    companies = {}

    # Find header row (try rows 1-10)
    header_row = None
    headers = {}
    for row_idx in range(1, 11):
        row_values = [str(cell.value or "").strip() for cell in sheet[row_idx]]
        # Look for "Company" or "Company Name" in the row
        for col_idx, val in enumerate(row_values):
            if val.lower() in ("company", "company name", "company_name"):
                header_row = row_idx
                headers = {val.lower(): col_idx for col_idx, val in enumerate(row_values) if val}
                break
        if header_row:
            break

    if not header_row:
        warnings.append("Could not find header row in Decision Matrix tab")
        return companies, warnings

    # Column mapping (flexible — matches various header naming conventions)
    col_map = _build_column_map(headers)

    # Parse data rows
    for row_idx in range(header_row + 1, sheet.max_row + 1):
        row = [cell.value for cell in sheet[row_idx]]

        company_name = _get_cell(row, col_map, "company_name")
        if not company_name or str(company_name).strip() == "":
            continue

        company_name = str(company_name).strip()

        try:
            company = Company(
                company_name=company_name,
                hq_country=str(_get_cell(row, col_map, "hq_country") or ""),
                region=str(_get_cell(row, col_map, "region") or ""),
                business_type=str(_get_cell(row, col_map, "business_type") or ""),
                countries_with_controlled_farms=str(_get_cell(row, col_map, "countries") or ""),
                main_crops=_parse_crops(_get_cell(row, col_map, "main_crops")),
                score_integration=_parse_float(_get_cell(row, col_map, "integration")),
                score_high_value_crop=_parse_float(_get_cell(row, col_map, "high_value_crop")),
                score_registration_ease=_parse_float(_get_cell(row, col_map, "registration_ease")),
                score_scale_potential=_parse_float(_get_cell(row, col_map, "scale_potential")),
                score_strategic_leverage=_parse_float(_get_cell(row, col_map, "strategic_leverage")),
                penalty_complexity=_parse_float(_get_cell(row, col_map, "penalty_complexity")),
                notes=str(_get_cell(row, col_map, "notes") or ""),
            )
            companies[company_name.lower()] = company
        except Exception as e:
            warnings.append(f"Row {row_idx}: Error parsing '{company_name}': {e}")

    return companies, warnings


def _import_target_list(sheet, companies: dict[str, Company], config: dict) -> list[str]:
    """Parse the Target List tab to add pipeline/hectare data."""
    warnings = []

    # Find header row
    header_row = None
    headers = {}
    for row_idx in range(1, 11):
        row_values = [str(cell.value or "").strip() for cell in sheet[row_idx]]
        for col_idx, val in enumerate(row_values):
            if val.lower() in ("company", "company name", "company_name"):
                header_row = row_idx
                headers = {val.lower(): col_idx for col_idx, val in enumerate(row_values) if val}
                break
        if header_row:
            break

    if not header_row:
        warnings.append("Could not find header row in Target List tab")
        return warnings

    col_map = _build_column_map(headers)

    for row_idx in range(header_row + 1, sheet.max_row + 1):
        row = [cell.value for cell in sheet[row_idx]]

        company_name = _get_cell(row, col_map, "company_name")
        if not company_name or str(company_name).strip() == "":
            continue

        company_name = str(company_name).strip()
        key = company_name.lower()

        if key in companies:
            company = companies[key]
            # Pipeline stage
            stage = _get_cell(row, col_map, "pipeline_stage")
            if stage:
                stage = str(stage).strip().upper()
                if stage in ("L0", "L1", "L2", "L3", "L4", "L5"):
                    company.pipeline_stage = stage

            # Hectares
            hectares = _get_cell(row, col_map, "hectares")
            if hectares is not None:
                company.hectares_controlled = _parse_float(hectares)

            # Owner
            owner = _get_cell(row, col_map, "owner")
            if owner:
                company.pipeline_owner = str(owner).strip()
        else:
            warnings.append(f"Target List company '{company_name}' not found in Decision Matrix")

    return warnings


def _import_assumptions(sheet, config: dict) -> None:
    """Try to parse assumptions from the Assumptions tab."""
    for row in sheet.iter_rows(min_row=1, max_row=sheet.max_row, values_only=True):
        if not row or not row[0]:
            continue
        label = str(row[0]).strip().lower()
        value = row[1] if len(row) > 1 else None
        if value is None:
            continue

        try:
            if "coverage" in label:
                config["revenue_assumptions"]["coverage_pct"] = float(value)
            elif "application rate" in label or "litres per ha" in label:
                config["revenue_assumptions"]["application_rate_litres_per_ha"] = float(value)
            elif "applications per" in label or "season" in label:
                config["revenue_assumptions"]["applications_per_season"] = int(float(value))
            elif "price" in label:
                config["revenue_assumptions"]["price_per_litre_eur"] = float(value)
        except (ValueError, TypeError):
            pass


def _build_column_map(headers: dict[str, int]) -> dict[str, int | None]:
    """Build a flexible column mapping from header names."""
    col_map = {
        "company_name": None,
        "hq_country": None,
        "region": None,
        "business_type": None,
        "countries": None,
        "main_crops": None,
        "integration": None,
        "high_value_crop": None,
        "registration_ease": None,
        "scale_potential": None,
        "strategic_leverage": None,
        "penalty_complexity": None,
        "notes": None,
        "pipeline_stage": None,
        "hectares": None,
        "owner": None,
    }

    # Mapping: our field -> possible header names (lowercase)
    aliases = {
        "company_name": ["company", "company name", "company_name", "name"],
        "hq_country": ["hq country", "hq_country", "country", "headquarters"],
        "region": ["region", "geographic region"],
        "business_type": ["business type", "business_type", "type", "business description"],
        "countries": ["countries with controlled farms", "countries_with_controlled_farms",
                      "countries", "farm countries", "controlled farms"],
        "main_crops": ["main crops", "main_crops", "main crops (top 5)", "crops", "top crops"],
        "integration": ["integration", "vertical integration", "score_integration",
                        "integration score"],
        "high_value_crop": ["high-value crop", "high value crop", "high_value_crop",
                            "crop exposure", "high-value crop exposure"],
        "registration_ease": ["registration ease", "registration_ease", "registration",
                              "reg ease"],
        "scale_potential": ["scale potential", "scale_potential", "scale"],
        "strategic_leverage": ["strategic leverage", "strategic_leverage", "leverage"],
        "penalty_complexity": ["penalty", "complexity penalty", "penalty_complexity",
                               "procurement complexity", "complexity"],
        "notes": ["notes", "evidence", "notes/evidence", "source", "comments"],
        "pipeline_stage": ["pipeline stage", "pipeline_stage", "stage", "pipeline",
                           "l-stage", "5 ls"],
        "hectares": ["hectares", "hectares_controlled", "ha", "hectares controlled",
                     "total hectares"],
        "owner": ["owner", "pipeline_owner", "assigned to", "lead", "responsible"],
    }

    for field, possible_names in aliases.items():
        for name in possible_names:
            if name in headers:
                col_map[field] = headers[name]
                break

    return col_map


def _get_cell(row: list, col_map: dict, field: str):
    """Get a cell value from a row using the column map."""
    idx = col_map.get(field)
    if idx is None or idx >= len(row):
        return None
    return row[idx]


def _parse_float(value) -> float:
    """Parse a value to float, returning 0.0 on failure."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _parse_crops(value) -> list[str]:
    """Parse a comma-separated crops string into a list."""
    if not value:
        return []
    return [c.strip() for c in str(value).split(",") if c.strip()]
