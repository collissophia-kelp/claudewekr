"""Import companies from existing Strategic Decision Matrix Excel workbook."""

from pathlib import Path

from openpyxl import load_workbook

from engine.models import Company
from engine.tags import auto_generate_tags


def import_xlsx(file_path: str, config: dict) -> tuple[list[Company], list[str]]:
    """Import companies from the Strategic Decision Matrix Excel file.

    Handles the actual workbook structure:
    - Matrix split across multiple tabs (Top 50, 51-100, 101-150)
    - Refined List tab
    - Target List with pipeline stage section headers
    - Removed Companies and Watch List tabs
    - Assumptions tab with weights and thresholds

    Returns (companies, warnings).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    wb = load_workbook(path, data_only=True)
    warnings = []

    # 1. Import assumptions first (updates config weights)
    if "Assumptions" in wb.sheetnames:
        _import_assumptions(wb["Assumptions"], config)

    # 2. Import from all Matrix tabs
    companies_dict: dict[str, Company] = {}
    matrix_tabs = [s for s in wb.sheetnames if s.startswith("Matrix -") and "Refined" not in s]

    if matrix_tabs:
        for tab_name in matrix_tabs:
            tab_companies, tab_warnings = _import_matrix_tab(wb[tab_name])
            warnings.extend(tab_warnings)
            for key, company in tab_companies.items():
                if key not in companies_dict:
                    companies_dict[key] = company
                else:
                    warnings.append(f"Duplicate company '{company.company_name}' in {tab_name}, skipped")
    else:
        warnings.append("No Matrix tabs found in workbook")

    # 3. Import from Refined List (may have companies not in the matrix tabs)
    if "Matrix - Refined list" in wb.sheetnames:
        refined_companies, refined_warnings = _import_matrix_tab(wb["Matrix - Refined list"])
        warnings.extend(refined_warnings)
        for key, company in refined_companies.items():
            if key not in companies_dict:
                companies_dict[key] = company

    # 4. Import Target List for pipeline stage, hectares, and notes
    if "Target List" in wb.sheetnames:
        target_warnings = _import_target_list(wb["Target List"], companies_dict)
        warnings.extend(target_warnings)

    # 5. Import Removed Companies
    if "Removed Companies" in wb.sheetnames:
        removed_warnings = _import_removed(wb["Removed Companies"], companies_dict)
        warnings.extend(removed_warnings)

    # 6. Import Watch List
    if "Watch List" in wb.sheetnames:
        watch_warnings = _import_watch_list(wb["Watch List"], companies_dict)
        warnings.extend(watch_warnings)

    # 7. Import Current Leads & Contacts for pipeline owner
    if "Current Leads & Contacts" in wb.sheetnames:
        leads_warnings = _import_leads(wb["Current Leads & Contacts"], companies_dict)
        warnings.extend(leads_warnings)

    # Auto-generate tags for all companies
    for company in companies_dict.values():
        company.tags = auto_generate_tags(company)

    wb.close()
    return list(companies_dict.values()), warnings


def _import_matrix_tab(sheet) -> tuple[dict[str, Company], list[str]]:
    """Parse a matrix tab. Header at row 4, data starts row 5+."""
    warnings = []
    companies = {}

    # Find header row with "Company" in column A
    header_row = None
    headers = {}
    for row_idx in range(1, 11):
        row_values = [str(cell.value or "").strip() for cell in sheet[row_idx]]
        for col_idx, val in enumerate(row_values):
            if val.lower() in ("company", "company name"):
                header_row = row_idx
                headers = {val.strip().lower(): col_idx for col_idx, val in enumerate(row_values) if val}
                break
        if header_row:
            break

    if not header_row:
        warnings.append(f"No header row found in '{sheet.title}'")
        return companies, warnings

    col_map = _build_matrix_column_map(headers)

    # Parse data rows
    for row_idx in range(header_row + 1, sheet.max_row + 1):
        row = [cell.value for cell in sheet[row_idx]]

        name = _get(row, col_map, "company")
        if not name or str(name).strip() == "":
            continue

        name = str(name).strip()

        # Skip section header rows (e.g. "Top 50 food companies in the world")
        hq = _get(row, col_map, "hq_country")
        if not hq or str(hq).strip() == "":
            continue

        # Parse scores — some cells may be empty or contain formulas
        integration = _parse_score(_get(row, col_map, "integration"))
        hvc = _parse_score(_get(row, col_map, "high_value_crop"))
        reg = _parse_score(_get(row, col_map, "registration_ease"))
        scale = _parse_score(_get(row, col_map, "scale_potential"))
        leverage = _parse_score(_get(row, col_map, "strategic_leverage"))
        penalty = _parse_score(_get(row, col_map, "penalty"))

        owner_val = _get(row, col_map, "owner")

        try:
            company = Company(
                company_name=name,
                hq_country=str(hq).strip(),
                region=str(_get(row, col_map, "region") or "").strip(),
                business_type=str(_get(row, col_map, "business_type") or "").strip(),
                countries_with_controlled_farms=str(_get(row, col_map, "countries") or "").strip(),
                main_crops=_parse_crops(_get(row, col_map, "main_crops")),
                score_integration=integration,
                score_high_value_crop=hvc,
                score_registration_ease=reg,
                score_scale_potential=scale,
                score_strategic_leverage=leverage,
                penalty_complexity=penalty,
                pipeline_owner=str(owner_val).strip() if owner_val else "",
                notes=str(_get(row, col_map, "notes") or "").strip(),
            )
            companies[name.lower()] = company
        except Exception as e:
            warnings.append(f"'{sheet.title}' row {row_idx}: Error parsing '{name}': {e}")

    return companies, warnings


def _import_target_list(sheet, companies: dict[str, Company]) -> list[str]:
    """Parse the Target List tab with pipeline stage section headers.

    Structure:
      Row 4: headers (Company, HQ Country, Business Type, Main Focus Crops, Score, Tier, Revenue, Hectares, Notes)
      Row 5+: Mix of:
        - Stage headers: "L5 — Under Contract", "L4 — Defining Contract", etc.
        - Region sub-headers: "    Latin America", "    North America", etc.
        - Company data rows
        - Info rows: "    No companies at this stage currently"
    """
    warnings = []
    current_stage = "L0"

    # Stage mapping from section header text
    stage_map = {
        "l5": "L5", "under contract": "L5",
        "l4": "L4", "defining contract": "L4",
        "l3": "L3", "qualifying": "L3",
        "l2": "L2", "active engagement": "L2", "our active": "L2",
        "l1": "L1", "identified": "L1",
        "l0": "L0", "watch": "L0", "pre-pipeline": "L0",
    }

    # Summary/total rows to skip
    skip_keywords = [
        "total companies", "tier 1", "tier 2", "tier 3", "tier 4",
        "unscored", "total addressable", "total y", "subtotal",
        "grand total", "summary", "revenue model",
    ]

    for row_idx in range(5, sheet.max_row + 1):
        row = [cell.value for cell in sheet[row_idx]]
        first_cell = str(row[0] or "").strip()

        if not first_cell:
            continue

        first_lower = first_cell.lower()

        # Skip summary/total rows
        if any(kw in first_lower for kw in skip_keywords):
            continue

        # Check if this is a stage header
        is_stage_header = False
        for key, stage in stage_map.items():
            if key in first_lower:
                current_stage = stage
                is_stage_header = True
                break

        if is_stage_header:
            continue

        # Skip region sub-headers and info rows (no HQ country in col B)
        hq = row[1] if len(row) > 1 else None
        if not hq or str(hq).strip() == "":
            continue

        company_name = first_cell
        hq_country = str(hq).strip()
        business_type = str(row[2] or "").strip() if len(row) > 2 else ""
        crops_str = str(row[3] or "").strip() if len(row) > 3 else ""
        score_val = row[4] if len(row) > 4 else None
        tier_val = row[5] if len(row) > 5 else None
        revenue_val = row[6] if len(row) > 6 else None
        hectares_val = row[7] if len(row) > 7 else None
        notes_val = str(row[8] or "").strip() if len(row) > 8 else ""

        key = company_name.lower()
        hectares = _parse_float(hectares_val)

        # Try exact match first, then fuzzy match
        matched_key = _fuzzy_find(key, companies)

        if matched_key:
            company = companies[matched_key]
            company.pipeline_stage = current_stage
            if hectares > 0:
                company.hectares_controlled = hectares
            if notes_val and (not company.notes or len(notes_val) > len(company.notes)):
                company.notes = notes_val
        else:
            # Company only in Target List (not in matrix) — create new entry
            company = Company(
                company_name=company_name,
                hq_country=hq_country,
                business_type=business_type,
                main_crops=_parse_crops(crops_str),
                pipeline_stage=current_stage,
                hectares_controlled=hectares,
                notes=notes_val,
            )
            companies[key] = company
            warnings.append(f"Target List company '{company_name}' added (not in Matrix tabs)")

    return warnings


def _import_removed(sheet, companies: dict[str, Company]) -> list[str]:
    """Import Removed Companies tab."""
    warnings = []

    for row_idx in range(2, sheet.max_row + 1):
        row = [cell.value for cell in sheet[row_idx]]
        name = str(row[0] or "").strip()
        if not name:
            continue

        key = name.lower()
        reason = str(row[7] or "").strip() if len(row) > 7 else "Removed"

        if key in companies:
            companies[key].excluded = True
            companies[key].exclusion_reason = reason
        else:
            # Create a minimal record for removed companies
            company = Company(
                company_name=name,
                hq_country=str(row[1] or "").strip() if len(row) > 1 else "",
                region=str(row[2] or "").strip() if len(row) > 2 else "",
                business_type=str(row[3] or "").strip() if len(row) > 3 else "",
                main_crops=_parse_crops(row[4] if len(row) > 4 else None),
                excluded=True,
                exclusion_reason=reason,
            )
            score_val = _parse_score(row[5] if len(row) > 5 else None)
            if score_val > 0:
                # This is the weighted score, not raw — we can't decompose it
                pass
            companies[key] = company

    return warnings


def _import_watch_list(sheet, companies: dict[str, Company]) -> list[str]:
    """Import Watch List tab."""
    warnings = []

    for row_idx in range(2, sheet.max_row + 1):
        row = [cell.value for cell in sheet[row_idx]]
        name = str(row[0] or "").strip()
        if not name:
            continue

        key = name.lower()
        why_watch = str(row[7] or "").strip() if len(row) > 7 else ""
        trigger = str(row[8] or "").strip() if len(row) > 8 else ""

        note = f"WATCH: {why_watch}"
        if trigger:
            note += f" | Re-entry: {trigger}"

        if key in companies:
            companies[key].pipeline_stage = "L0"
            if note:
                companies[key].notes = note
            companies[key].tags.append("strategic:watch_list")
        else:
            company = Company(
                company_name=name,
                hq_country=str(row[1] or "").strip() if len(row) > 1 else "",
                region=str(row[2] or "").strip() if len(row) > 2 else "",
                business_type=str(row[3] or "").strip() if len(row) > 3 else "",
                main_crops=_parse_crops(row[4] if len(row) > 4 else None),
                pipeline_stage="L0",
                notes=note,
                tags=["strategic:watch_list"],
            )
            companies[key] = company

    return warnings


def _import_leads(sheet, companies: dict[str, Company]) -> list[str]:
    """Import Current Leads & Contacts for pipeline owner info."""
    warnings = []

    current_stage = "L0"
    stage_map = {
        "l5": "L5", "under contract": "L5",
        "l4": "L4", "defining": "L4",
        "l3": "L3", "qualifying": "L3",
        "l2": "L2", "engaged": "L2", "active": "L2",
        "l1": "L1", "identified": "L1",
    }

    for row_idx in range(2, sheet.max_row + 1):
        row = [cell.value for cell in sheet[row_idx]]
        first_cell = str(row[0] or "").strip()

        if not first_cell:
            continue

        # Check if stage header
        first_lower = first_cell.lower()
        is_stage = False
        for key, stage in stage_map.items():
            if key in first_lower:
                current_stage = stage
                is_stage = True
                break
        if is_stage:
            continue

        # Try to find company and assign owner
        key = _fuzzy_find(first_cell.lower(), companies)
        if key:
            # Owner is typically in column 12-13 area (KB Owner)
            owner = None
            for col_idx in range(10, min(len(row), 16)):
                val = row[col_idx]
                if val and str(val).strip() in ("David", "Sophia", "Valentin", "Rynhardt"):
                    owner = str(val).strip()
                    break
            if owner:
                companies[key].pipeline_owner = owner

    return warnings


def _import_assumptions(sheet, config: dict) -> None:
    """Parse the Assumptions tab to update config weights and thresholds."""
    weight_map = {
        "integration": "integration",
        "high-value crop": "high_value_crop",
        "high value crop": "high_value_crop",
        "registration ease": "registration_ease",
        "scale potential": "scale_potential",
        "strategic leverage": "strategic_leverage",
        "penalty": "penalty_complexity",
        "complexity": "penalty_complexity",
    }

    for row in sheet.iter_rows(min_row=1, max_row=sheet.max_row, values_only=True):
        if not row or not row[0]:
            continue
        label = str(row[0]).strip().lower()
        value = row[1] if len(row) > 1 else None
        if value is None:
            continue

        try:
            val = float(value)
        except (ValueError, TypeError):
            continue

        # Weights
        for key, config_key in weight_map.items():
            if key in label:
                config["scoring_weights"][config_key] = val
                break

        # Tier thresholds
        if "tier 1" in label:
            config["tier_thresholds"]["tier_1_min"] = val
        elif "tier 2" in label:
            config["tier_thresholds"]["tier_2_min"] = val
        elif "tier 3" in label:
            config["tier_thresholds"]["tier_3_min"] = val


def _fuzzy_find(name: str, companies: dict[str, Company]) -> str | None:
    """Find a company key by exact or fuzzy match.

    Tries: exact match, substring match, parenthetical match.
    E.g. "Dole plc" matches "Total Produce (Dole plc)"
    """
    name_lower = name.lower()

    # Exact match
    if name_lower in companies:
        return name_lower

    # Check if any existing company name contains this name or vice versa
    for key in companies:
        if name_lower in key or key in name_lower:
            return key

    # Check parenthetical names: "Total Produce (Dole plc)" matches "Dole plc"
    for key, company in companies.items():
        cname = company.company_name.lower()
        if "(" in cname:
            paren_content = cname.split("(")[1].rstrip(")")
            if name_lower == paren_content or paren_content in name_lower:
                return key

    return None


def _build_matrix_column_map(headers: dict[str, int]) -> dict[str, int | None]:
    """Build column mapping from matrix tab headers."""
    aliases = {
        "company": ["company", "company name"],
        "hq_country": ["hq country"],
        "region": ["region"],
        "business_type": ["business type (eg. integrated producer)", "business type"],
        "countries": ["countries with controlled farms"],
        "main_crops": ["main crops (top 5)", "main crops"],
        "integration": ["integration / owns land (0–5)", "integration / owns land",
                        "integration"],
        "high_value_crop": ["high-value crop exposure (0–5)", "high-value crop exposure",
                            "high value crop exposure"],
        "registration_ease": ["registration ease (0–5)", "registration ease"],
        "scale_potential": ["scale potential (0–5)", "scale potential"],
        "strategic_leverage": ["strategic leverage (0–5)", "strategic leverage"],
        "penalty": ["penalty: complexity (0–-2)", "penalty: complexity",
                    "penalty complexity", "penalty"],
        "notes": ["notes / evidence", "notes/evidence", "notes"],
        "owner": ["owner"],
    }

    col_map = {}
    for field, possible_names in aliases.items():
        col_map[field] = None
        for name in possible_names:
            if name in headers:
                col_map[field] = headers[name]
                break

    return col_map


def _get(row: list, col_map: dict, field: str):
    """Get a cell value from a row using the column map."""
    idx = col_map.get(field)
    if idx is None or idx >= len(row):
        return None
    return row[idx]


def _parse_score(value) -> float:
    """Parse a score value, handling empty cells and non-numeric values."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if s in ("", "—", "-", "NA", "N/A", "n/a"):
        return 0.0
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _parse_float(value) -> float:
    """Parse a value to float, returning 0.0 on failure."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(",", "")
    if s in ("", "—", "-", "unknown", "Unknown", "NA"):
        return 0.0
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _parse_crops(value) -> list[str]:
    """Parse a comma-separated crops string into a list."""
    if not value:
        return []
    return [c.strip() for c in str(value).split(",") if c.strip()]
