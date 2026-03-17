"""Terminal rendering of pivot summaries by region and produce type."""

from rich.console import Console
from rich.table import Table

from engine.models import Company
from engine.scoring import score_company
from engine.revenue import calculate_revenue

console = Console()


def render_region_pivot(companies: list[Company], config: dict) -> None:
    """Render a region pivot summary table."""
    regions: dict[str, dict] = {}

    for c in companies:
        if c.excluded:
            continue
        ws, t, tl = score_company(c, config)
        rev = calculate_revenue(c, config)
        r = c.region or "Unknown"

        if r not in regions:
            regions[r] = {"t1": 0, "t2": 0, "t3": 0, "t4": 0,
                          "total": 0, "hectares": 0.0, "revenue": 0.0}
        regions[r][f"t{t}"] += 1
        regions[r]["total"] += 1
        regions[r]["hectares"] += c.hectares_controlled
        regions[r]["revenue"] += rev

    table = Table(title="By Region")
    table.add_column("Region", style="bold")
    table.add_column("Tier 1", justify="right", style="bold green")
    table.add_column("Tier 2", justify="right", style="green")
    table.add_column("Tier 3", justify="right", style="yellow")
    table.add_column("Total", justify="right")
    table.add_column("Hectares", justify="right")
    table.add_column("Y5 Revenue", justify="right")

    for r, data in sorted(regions.items(), key=lambda x: -x[1]["revenue"]):
        table.add_row(
            r, str(data["t1"]), str(data["t2"]), str(data["t3"]),
            str(data["total"]), f"{data['hectares']:,.0f}",
            f"\u20ac{data['revenue']:,.0f}",
        )

    console.print(table)


def render_produce_pivot(companies: list[Company], config: dict) -> None:
    """Render a produce type pivot summary table."""
    crops: dict[str, dict] = {}

    for c in companies:
        if c.excluded:
            continue
        ws, _, _, _ = score_company(c, config)  # ws is second return
        ws_val, t, tl = score_company(c, config)
        rev = calculate_revenue(c, config)

        for crop in c.main_crops:
            crop = crop.strip()
            if not crop:
                continue
            if crop not in crops:
                crops[crop] = {"count": 0, "total_score": 0.0,
                               "hectares": 0.0, "revenue": 0.0}
            crops[crop]["count"] += 1
            crops[crop]["total_score"] += ws_val
            crops[crop]["hectares"] += c.hectares_controlled
            crops[crop]["revenue"] += rev

    table = Table(title="By Produce Type")
    table.add_column("Crop", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Avg Score", justify="right")
    table.add_column("Hectares", justify="right")
    table.add_column("Y5 Revenue", justify="right")

    for crop, data in sorted(crops.items(), key=lambda x: -x[1]["count"]):
        avg = data["total_score"] / data["count"] if data["count"] > 0 else 0
        table.add_row(
            crop, str(data["count"]), f"{avg:.2f}",
            f"{data['hectares']:,.0f}", f"\u20ac{data['revenue']:,.0f}",
        )

    console.print(table)
