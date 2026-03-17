"""Export board-ready Excel workbook with live formulas and professional formatting."""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from engine.config import load_scoring_guide
from engine.models import Company
from engine.scoring import score_company, calculate_weighted_score, assign_tier
from engine.revenue import calculate_revenue
from engine.pipeline import STAGE_ORDER
from data_io.formatters import (
    apply_header_row, apply_data_cell, apply_tier_formatting,
    write_section_header, set_column_widths, freeze_header,
    add_autofilter, setup_print_area,
    CURRENCY_EUR_FORMAT, SCORE_FORMAT, BOLD_FONT, THIN_BORDER,
    DATA_FONT,
)


def export_workbook(companies: list[Company], config: dict, output_path: str,
                    min_stage: str | None = None) -> None:
    """Generate the full multi-tab board-ready workbook."""
    wb = Workbook()

    # Remove default sheet
    wb.remove(wb.active)

    active = [c for c in companies if not c.excluded]

    # Score all companies
    scored = [(c, *score_company(c, config)) for c in active]
    scored.sort(key=lambda x: -x[1])

    # Tab 1: Full Matrix
    _write_full_matrix(wb, scored, config)

    # Tab 2: Refined List
    _write_refined_list(wb, scored, config)

    # Tab 3: Target List
    _write_target_list(wb, scored, config, min_stage)

    # Tab 4: By Region
    _write_region_pivot(wb, scored, config)

    # Tab 5: By Produce Type
    _write_produce_pivot(wb, scored, config)

    # Tab 6: Pipeline Funnel
    _write_pipeline_funnel(wb, scored, config)

    # Tab 7: Scoring Guide
    _write_scoring_guide(wb)

    # Tab 8: Assumptions
    assumptions_row = _write_assumptions(wb, config)

    wb.save(output_path)


def _write_full_matrix(wb: Workbook, scored: list, config: dict) -> None:
    """Tab 1: Full Matrix — all companies sorted by weighted score."""
    ws = wb.create_sheet("Full Matrix")
    headers = [
        "Company", "HQ", "Region", "Business Type", "Countries", "Main Crops",
        "Integration", "High-Value Crop", "Reg. Ease", "Scale", "Leverage", "Penalty",
        "Weighted Score", "Tier", "Stage", "Notes",
    ]

    # Write headers
    for i, h in enumerate(headers, 1):
        ws.cell(row=1, column=i, value=h)
    apply_header_row(ws, 1, len(headers))

    # Write data
    weights = config["scoring_weights"]
    for row_idx, (c, ws_val, tier, tl) in enumerate(scored, 2):
        values = [
            c.company_name, c.hq_country, c.region, c.business_type,
            c.countries_with_controlled_farms, ", ".join(c.main_crops),
            c.score_integration, c.score_high_value_crop, c.score_registration_ease,
            c.score_scale_potential, c.score_strategic_leverage, c.penalty_complexity,
        ]

        for col_idx, val in enumerate(values, 1):
            fmt = SCORE_FORMAT if col_idx >= 7 else None
            apply_data_cell(ws, row_idx, col_idx, val, fmt)

        # Weighted score with LIVE formula
        score_cols = {
            7: weights["integration"],
            8: weights["high_value_crop"],
            9: weights["registration_ease"],
            10: weights["scale_potential"],
            11: weights["strategic_leverage"],
            12: weights["penalty_complexity"],
        }
        formula_parts = []
        for col, weight in score_cols.items():
            col_letter = get_column_letter(col)
            formula_parts.append(f"{col_letter}{row_idx}*{weight}")
        formula = "=" + "+".join(formula_parts)
        apply_data_cell(ws, row_idx, 13, formula, SCORE_FORMAT)

        # Tier (display value)
        apply_data_cell(ws, row_idx, 14, tl)
        apply_tier_formatting(ws, row_idx, 14, tier, len(headers))

        # Stage
        apply_data_cell(ws, row_idx, 15, c.pipeline_stage)

        # Notes
        apply_data_cell(ws, row_idx, 16, c.notes)

    set_column_widths(ws, headers)
    freeze_header(ws)
    add_autofilter(ws, len(headers))
    setup_print_area(ws, len(headers))


def _write_refined_list(wb: Workbook, scored: list, config: dict) -> None:
    """Tab 2: Refined List — Tier 1-3, exclusions applied."""
    ws = wb.create_sheet("Refined List")

    # Filter: Tier 1-3 only, no exclusion-tagged companies
    refined = [(c, ws_val, tier, tl) for c, ws_val, tier, tl in scored
               if tier <= 3 and not any(t.startswith("exclude:") for t in c.tags)]
    refined.sort(key=lambda x: (x[2], -x[1]))  # tier asc, score desc

    headers = [
        "Company", "HQ", "Region", "Business Type", "Countries", "Main Crops",
        "Integration", "High-Value Crop", "Reg. Ease", "Scale", "Leverage", "Penalty",
        "Weighted Score", "Tier", "Stage", "Notes",
    ]

    for i, h in enumerate(headers, 1):
        ws.cell(row=1, column=i, value=h)
    apply_header_row(ws, 1, len(headers))

    weights = config["scoring_weights"]
    for row_idx, (c, ws_val, tier, tl) in enumerate(refined, 2):
        values = [
            c.company_name, c.hq_country, c.region, c.business_type,
            c.countries_with_controlled_farms, ", ".join(c.main_crops),
            c.score_integration, c.score_high_value_crop, c.score_registration_ease,
            c.score_scale_potential, c.score_strategic_leverage, c.penalty_complexity,
        ]

        for col_idx, val in enumerate(values, 1):
            fmt = SCORE_FORMAT if col_idx >= 7 else None
            apply_data_cell(ws, row_idx, col_idx, val, fmt)

        # Live formula for weighted score
        score_cols = {7: weights["integration"], 8: weights["high_value_crop"],
                      9: weights["registration_ease"], 10: weights["scale_potential"],
                      11: weights["strategic_leverage"], 12: weights["penalty_complexity"]}
        formula_parts = [f"{get_column_letter(col)}{row_idx}*{w}" for col, w in score_cols.items()]
        apply_data_cell(ws, row_idx, 13, "=" + "+".join(formula_parts), SCORE_FORMAT)

        apply_data_cell(ws, row_idx, 14, tl)
        apply_tier_formatting(ws, row_idx, 14, tier, len(headers))
        apply_data_cell(ws, row_idx, 15, c.pipeline_stage)
        apply_data_cell(ws, row_idx, 16, c.notes)

    set_column_widths(ws, headers)
    freeze_header(ws)
    add_autofilter(ws, len(headers))
    setup_print_area(ws, len(headers))


def _write_target_list(wb: Workbook, scored: list, config: dict,
                       min_stage: str | None = None) -> None:
    """Tab 3: Target List — L1+ companies grouped by pipeline stage."""
    ws = wb.create_sheet("Target List")

    min_idx = STAGE_ORDER.index(min_stage) if min_stage and min_stage in STAGE_ORDER else 1  # L1
    targets = [(c, ws_val, tier, tl) for c, ws_val, tier, tl in scored
               if STAGE_ORDER.index(c.pipeline_stage) >= min_idx]

    headers = [
        "Company", "HQ", "Region", "Business Type", "Main Crops",
        "Hectares", "Score", "Tier", "Y5 Revenue", "Owner", "Notes",
    ]
    num_cols = len(headers)

    for i, h in enumerate(headers, 1):
        ws.cell(row=1, column=i, value=h)
    apply_header_row(ws, 1, num_cols)

    assumptions = config["revenue_assumptions"]
    row = 2
    grand_total_rev = 0.0

    # Group by stage (L5 first)
    for stage in reversed(STAGE_ORDER):
        stage_idx = STAGE_ORDER.index(stage)
        if stage_idx < min_idx:
            continue

        stage_companies = [(c, ws, t, tl) for c, ws, t, tl in targets
                           if c.pipeline_stage == stage]
        if not stage_companies:
            continue

        # Sort within stage: by region, then score desc
        stage_companies.sort(key=lambda x: (x[0].region, -x[1]))

        # Section header
        stage_name = config["pipeline_stages"].get(stage, stage)
        write_section_header(ws, row, f"{stage} — {stage_name}", num_cols)
        row += 1

        stage_rev_total = 0.0
        first_data_row = row

        for c, ws_val, tier, tl in stage_companies:
            rev = calculate_revenue(c, config)

            apply_data_cell(ws, row, 1, c.company_name)
            apply_data_cell(ws, row, 2, c.hq_country)
            apply_data_cell(ws, row, 3, c.region)
            apply_data_cell(ws, row, 4, c.business_type)
            apply_data_cell(ws, row, 5, ", ".join(c.main_crops))
            apply_data_cell(ws, row, 6, c.hectares_controlled, "#,##0")
            apply_data_cell(ws, row, 7, ws_val, SCORE_FORMAT)
            apply_data_cell(ws, row, 8, tl)
            apply_tier_formatting(ws, row, 8, tier, num_cols)

            # Revenue with LIVE formula referencing hectares column
            # Y5 Rev = Hectares * coverage * rate * apps * price
            cov = assumptions["coverage_pct"]
            rate = assumptions["application_rate_litres_per_ha"]
            apps = assumptions["applications_per_season"]
            price = assumptions["price_per_litre_eur"]

            # Use per-company overrides if present
            if c.override_coverage_pct is not None:
                cov = c.override_coverage_pct
            if c.override_application_rate is not None:
                rate = c.override_application_rate
            if c.override_applications_per_season is not None:
                apps = c.override_applications_per_season
            if c.override_price_per_litre is not None:
                price = c.override_price_per_litre

            ha_col = get_column_letter(6)
            revenue_formula = f"={ha_col}{row}*{cov}*{rate}*{apps}*{price}"
            apply_data_cell(ws, row, 9, revenue_formula, CURRENCY_EUR_FORMAT)

            apply_data_cell(ws, row, 10, c.pipeline_owner)
            apply_data_cell(ws, row, 11, c.notes)

            stage_rev_total += rev
            row += 1

        # Subtotal row
        last_data_row = row - 1
        rev_col = get_column_letter(9)
        ha_col = get_column_letter(6)

        cell = ws.cell(row=row, column=5, value=f"{stage} Subtotal")
        cell.font = BOLD_FONT
        cell.border = THIN_BORDER

        # Hectares subtotal
        ha_formula = f"=SUM({ha_col}{first_data_row}:{ha_col}{last_data_row})"
        apply_data_cell(ws, row, 6, ha_formula, "#,##0")
        ws.cell(row=row, column=6).font = BOLD_FONT

        # Revenue subtotal
        rev_formula = f"=SUM({rev_col}{first_data_row}:{rev_col}{last_data_row})"
        apply_data_cell(ws, row, 9, rev_formula, CURRENCY_EUR_FORMAT)
        ws.cell(row=row, column=9).font = BOLD_FONT

        grand_total_rev += stage_rev_total
        row += 1  # blank row between sections

    # Grand total
    row += 1
    cell = ws.cell(row=row, column=5, value="GRAND TOTAL")
    cell.font = BOLD_FONT
    cell.border = THIN_BORDER

    total_ha = sum(c.hectares_controlled for c, _, _, _ in targets)
    total_rev = sum(calculate_revenue(c, config) for c, _, _, _ in targets)
    apply_data_cell(ws, row, 6, total_ha, "#,##0")
    ws.cell(row=row, column=6).font = BOLD_FONT
    apply_data_cell(ws, row, 9, total_rev, CURRENCY_EUR_FORMAT)
    ws.cell(row=row, column=9).font = BOLD_FONT

    set_column_widths(ws, headers)
    freeze_header(ws)
    setup_print_area(ws, num_cols)


def _write_region_pivot(wb: Workbook, scored: list, config: dict) -> None:
    """Tab 4: By Region — pivot summary."""
    ws = wb.create_sheet("By Region")

    headers = ["Region", "Tier 1", "Tier 2", "Tier 3", "Total", "Total Hectares", "Total Y5 Revenue"]
    for i, h in enumerate(headers, 1):
        ws.cell(row=1, column=i, value=h)
    apply_header_row(ws, 1, len(headers))

    # Aggregate
    regions: dict[str, dict] = {}
    for c, ws_val, tier, tl in scored:
        r = c.region or "Unknown"
        if r not in regions:
            regions[r] = {"t1": 0, "t2": 0, "t3": 0, "total": 0, "hectares": 0.0, "revenue": 0.0}
        regions[r]["total"] += 1
        if tier == 1:
            regions[r]["t1"] += 1
        elif tier == 2:
            regions[r]["t2"] += 1
        elif tier == 3:
            regions[r]["t3"] += 1
        regions[r]["hectares"] += c.hectares_controlled
        regions[r]["revenue"] += calculate_revenue(c, config)

    # Sort by revenue desc
    sorted_regions = sorted(regions.items(), key=lambda x: -x[1]["revenue"])

    for row_idx, (region, data) in enumerate(sorted_regions, 2):
        apply_data_cell(ws, row_idx, 1, region)
        apply_data_cell(ws, row_idx, 2, data["t1"])
        apply_data_cell(ws, row_idx, 3, data["t2"])
        apply_data_cell(ws, row_idx, 4, data["t3"])
        apply_data_cell(ws, row_idx, 5, data["total"])
        apply_data_cell(ws, row_idx, 6, data["hectares"], "#,##0")
        apply_data_cell(ws, row_idx, 7, data["revenue"], CURRENCY_EUR_FORMAT)

    set_column_widths(ws, headers)
    freeze_header(ws)
    setup_print_area(ws, len(headers))


def _write_produce_pivot(wb: Workbook, scored: list, config: dict) -> None:
    """Tab 5: By Produce Type — pivot summary."""
    ws = wb.create_sheet("By Produce Type")

    headers = ["Crop", "Count", "Avg Score", "Total Hectares", "Total Y5 Revenue"]
    for i, h in enumerate(headers, 1):
        ws.cell(row=1, column=i, value=h)
    apply_header_row(ws, 1, len(headers))

    # Aggregate by crop
    crops: dict[str, dict] = {}
    for c, ws_val, tier, tl in scored:
        rev = calculate_revenue(c, config)
        for crop in c.main_crops:
            crop = crop.strip()
            if not crop:
                continue
            if crop not in crops:
                crops[crop] = {"count": 0, "total_score": 0.0, "hectares": 0.0, "revenue": 0.0}
            crops[crop]["count"] += 1
            crops[crop]["total_score"] += ws_val
            crops[crop]["hectares"] += c.hectares_controlled
            crops[crop]["revenue"] += rev

    sorted_crops = sorted(crops.items(), key=lambda x: -x[1]["count"])

    for row_idx, (crop, data) in enumerate(sorted_crops, 2):
        avg_score = data["total_score"] / data["count"] if data["count"] > 0 else 0
        apply_data_cell(ws, row_idx, 1, crop)
        apply_data_cell(ws, row_idx, 2, data["count"])
        apply_data_cell(ws, row_idx, 3, avg_score, SCORE_FORMAT)
        apply_data_cell(ws, row_idx, 4, data["hectares"], "#,##0")
        apply_data_cell(ws, row_idx, 5, data["revenue"], CURRENCY_EUR_FORMAT)

    set_column_widths(ws, headers)
    freeze_header(ws)
    setup_print_area(ws, len(headers))


def _write_pipeline_funnel(wb: Workbook, scored: list, config: dict) -> None:
    """Tab 6: Pipeline Funnel."""
    ws = wb.create_sheet("Pipeline Funnel")

    headers = ["Stage", "Name", "Count", "Total Hectares", "Total Y5 Revenue", "Key Companies"]
    for i, h in enumerate(headers, 1):
        ws.cell(row=1, column=i, value=h)
    apply_header_row(ws, 1, len(headers))

    stage_names = config["pipeline_stages"]
    row = 2

    for stage in reversed(STAGE_ORDER):
        stage_companies = [(c, ws_val) for c, ws_val, _, _ in scored
                           if c.pipeline_stage == stage]
        total_ha = sum(c.hectares_controlled for c, _ in stage_companies)
        revenues = [(c, calculate_revenue(c, config)) for c, _ in stage_companies]
        total_rev = sum(r for _, r in revenues)

        # Top 3
        revenues.sort(key=lambda x: -x[1])
        top_names = ", ".join(c.company_name for c, r in revenues[:3])

        apply_data_cell(ws, row, 1, stage)
        apply_data_cell(ws, row, 2, stage_names.get(stage, ""))
        apply_data_cell(ws, row, 3, len(stage_companies))
        apply_data_cell(ws, row, 4, total_ha, "#,##0")
        apply_data_cell(ws, row, 5, total_rev, CURRENCY_EUR_FORMAT)
        apply_data_cell(ws, row, 6, top_names)
        row += 1

    # Total row
    apply_data_cell(ws, row, 1, "TOTAL")
    ws.cell(row=row, column=1).font = BOLD_FONT
    total_companies = len(scored)
    total_ha = sum(c.hectares_controlled for c, _, _, _ in scored)
    total_rev = sum(calculate_revenue(c, config) for c, _, _, _ in scored)
    apply_data_cell(ws, row, 3, total_companies)
    ws.cell(row=row, column=3).font = BOLD_FONT
    apply_data_cell(ws, row, 4, total_ha, "#,##0")
    ws.cell(row=row, column=4).font = BOLD_FONT
    apply_data_cell(ws, row, 5, total_rev, CURRENCY_EUR_FORMAT)
    ws.cell(row=row, column=5).font = BOLD_FONT

    set_column_widths(ws, headers)
    freeze_header(ws)
    setup_print_area(ws, len(headers))


def _write_scoring_guide(wb: Workbook) -> None:
    """Tab 7: Scoring Guide."""
    ws = wb.create_sheet("Scoring Guide")

    try:
        guide = load_scoring_guide()
    except FileNotFoundError:
        ws.cell(row=1, column=1, value="Scoring guide file not found")
        return

    criteria = guide.get("criteria", {})
    row = 1

    for criterion_key, criterion in criteria.items():
        # Criterion header
        ws.cell(row=row, column=1, value=criterion["name"])
        ws.cell(row=row, column=1).font = BOLD_FONT
        ws.cell(row=row, column=2, value=f"Weight: {criterion['weight']}")
        ws.cell(row=row, column=3, value=criterion["description"])
        row += 1

        # Score headers
        ws.cell(row=row, column=1, value="Score")
        ws.cell(row=row, column=2, value="Definition")
        apply_header_row(ws, row, 2)
        row += 1

        # Score definitions
        for score, definition in sorted(criterion["scores"].items(), key=lambda x: float(x[0])):
            apply_data_cell(ws, row, 1, float(score))
            apply_data_cell(ws, row, 2, definition)
            row += 1

        row += 1  # blank row between criteria

    ws.column_dimensions["A"].width = 15
    ws.column_dimensions["B"].width = 80
    ws.column_dimensions["C"].width = 60
    setup_print_area(ws, 3)


def _write_assumptions(wb: Workbook, config: dict) -> int:
    """Tab 8: Assumptions — all configurable values with named ranges."""
    ws = wb.create_sheet("Assumptions")

    headers = ["Parameter", "Value"]
    for i, h in enumerate(headers, 1):
        ws.cell(row=1, column=i, value=h)
    apply_header_row(ws, 1, 2)

    row = 2

    # Scoring Weights
    ws.cell(row=row, column=1, value="SCORING WEIGHTS")
    ws.cell(row=row, column=1).font = BOLD_FONT
    row += 1
    for key, val in config["scoring_weights"].items():
        apply_data_cell(ws, row, 1, key)
        apply_data_cell(ws, row, 2, val)

        # Create named range
        range_name = f"weight_{key}"
        try:
            from openpyxl.workbook.defined_name import DefinedName
            ref = f"Assumptions!$B${row}"
            dn = DefinedName(range_name, attr_text=ref)
            wb.defined_names.add(dn)
        except Exception:
            pass
        row += 1

    row += 1

    # Tier Thresholds
    ws.cell(row=row, column=1, value="TIER THRESHOLDS")
    ws.cell(row=row, column=1).font = BOLD_FONT
    row += 1
    for key, val in config["tier_thresholds"].items():
        apply_data_cell(ws, row, 1, key)
        apply_data_cell(ws, row, 2, val)
        row += 1

    row += 1

    # Revenue Assumptions
    ws.cell(row=row, column=1, value="REVENUE ASSUMPTIONS")
    ws.cell(row=row, column=1).font = BOLD_FONT
    row += 1
    rev_start_row = row
    for key, val in config["revenue_assumptions"].items():
        apply_data_cell(ws, row, 1, key)
        apply_data_cell(ws, row, 2, val)

        # Named ranges for revenue formula references
        range_name = f"rev_{key}"
        try:
            from openpyxl.workbook.defined_name import DefinedName
            ref = f"Assumptions!$B${row}"
            dn = DefinedName(range_name, attr_text=ref)
            wb.defined_names.add(dn)
        except Exception:
            pass
        row += 1

    row += 1

    # Pipeline Stages
    ws.cell(row=row, column=1, value="PIPELINE STAGES")
    ws.cell(row=row, column=1).font = BOLD_FONT
    row += 1
    for key, val in config["pipeline_stages"].items():
        apply_data_cell(ws, row, 1, key)
        apply_data_cell(ws, row, 2, val)
        row += 1

    ws.column_dimensions["A"].width = 35
    ws.column_dimensions["B"].width = 40
    setup_print_area(ws, 2)

    return rev_start_row
