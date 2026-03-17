"""Excel formatting helpers for board-ready workbook output."""

from openpyxl.styles import (
    Alignment, Border, Font, NamedStyle, PatternFill, Side, numbers
)
from openpyxl.utils import get_column_letter


# ── Colours ──────────────────────────────────────────────────────────

HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
HEADER_FONT = Font(name="Arial", size=10, bold=True, color="FFFFFF")
SECTION_FILL = PatternFill(start_color="8DB4E2", end_color="8DB4E2", fill_type="solid")
SECTION_FONT = Font(name="Arial", size=12, bold=True, color="000000")
DATA_FONT = Font(name="Arial", size=10)
BOLD_FONT = Font(name="Arial", size=10, bold=True)

TIER_FILLS = {
    1: PatternFill(start_color="548235", end_color="548235", fill_type="solid"),  # Dark green
    2: PatternFill(start_color="A9D08E", end_color="A9D08E", fill_type="solid"),  # Light green
    3: PatternFill(start_color="FFD966", end_color="FFD966", fill_type="solid"),  # Amber
    4: PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid"),  # Light grey
}
TIER_FONTS = {
    1: Font(name="Arial", size=10, bold=True, color="FFFFFF"),
    2: Font(name="Arial", size=10, color="000000"),
    3: Font(name="Arial", size=10, color="000000"),
    4: Font(name="Arial", size=10, color="808080"),
}

THIN_BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)

CURRENCY_FORMAT = '#,##0'
CURRENCY_EUR_FORMAT = '€#,##0'
SCORE_FORMAT = '0.00'
PCT_FORMAT = '0%'

# ── Column widths ────────────────────────────────────────────────────

DEFAULT_WIDTHS = {
    "Company": 35,
    "HQ": 15,
    "Region": 22,
    "Business Type": 30,
    "Countries": 35,
    "Main Crops": 30,
    "Integration": 12,
    "High-Value Crop": 14,
    "Reg. Ease": 12,
    "Scale": 12,
    "Leverage": 12,
    "Penalty": 12,
    "Weighted Score": 14,
    "Tier": 8,
    "Stage": 8,
    "Hectares": 12,
    "Y5 Revenue": 14,
    "Owner": 12,
    "Notes": 50,
    "Count": 10,
    "Total Hectares": 14,
    "Total Y5 Revenue": 16,
    "Avg Score": 12,
    "Key Companies": 40,
}


def apply_header_row(ws, row_num: int, num_cols: int) -> None:
    """Apply header formatting to a row."""
    for col in range(1, num_cols + 1):
        cell = ws.cell(row=row_num, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = THIN_BORDER


def apply_data_cell(ws, row_num: int, col_num: int, value, fmt: str | None = None) -> None:
    """Write and format a data cell."""
    cell = ws.cell(row=row_num, column=col_num, value=value)
    cell.font = DATA_FONT
    cell.border = THIN_BORDER
    cell.alignment = Alignment(vertical="center")
    if fmt:
        cell.number_format = fmt


def apply_tier_formatting(ws, row_num: int, tier_col: int, tier: int, num_cols: int) -> None:
    """Apply tier-based conditional formatting to a row."""
    fill = TIER_FILLS.get(tier)
    font = TIER_FONTS.get(tier)
    if fill:
        cell = ws.cell(row=row_num, column=tier_col)
        cell.fill = fill
        if font:
            cell.font = font


def write_section_header(ws, row_num: int, text: str, num_cols: int) -> None:
    """Write a section header row spanning all columns."""
    ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=num_cols)
    cell = ws.cell(row=row_num, column=1, value=text)
    cell.fill = SECTION_FILL
    cell.font = SECTION_FONT
    cell.alignment = Alignment(horizontal="left", vertical="center")
    cell.border = THIN_BORDER


def set_column_widths(ws, headers: list[str]) -> None:
    """Set column widths based on header names."""
    for i, header in enumerate(headers, 1):
        width = DEFAULT_WIDTHS.get(header, 15)
        ws.column_dimensions[get_column_letter(i)].width = width


def freeze_header(ws, row: int = 1) -> None:
    """Freeze panes below the header row."""
    ws.freeze_panes = f"A{row + 1}"


def add_autofilter(ws, num_cols: int, header_row: int = 1) -> None:
    """Add auto-filter to header row."""
    last_col = get_column_letter(num_cols)
    ws.auto_filter.ref = f"A{header_row}:{last_col}{ws.max_row}"


def setup_print_area(ws, num_cols: int) -> None:
    """Set print area and orientation."""
    from openpyxl.worksheet.page import PageMargins
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.page_margins = PageMargins(left=0.5, right=0.5, top=0.5, bottom=0.5)
    last_col = get_column_letter(num_cols)
    ws.print_area = f"A1:{last_col}{ws.max_row}"
