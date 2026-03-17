"""Terminal rendering of the full company matrix."""

from rich.console import Console
from rich.table import Table

from engine.models import Company
from engine.scoring import score_company
from engine.revenue import calculate_revenue

console = Console()


def render_matrix(companies: list[Company], config: dict, limit: int = 50) -> None:
    """Render the full matrix as a rich table."""
    scored = [(c, *score_company(c, config)) for c in companies if not c.excluded]
    scored.sort(key=lambda x: -x[1])

    table = Table(title=f"Full Matrix ({len(scored)} companies)")
    table.add_column("Company", style="bold", max_width=30)
    table.add_column("Region", max_width=18)
    table.add_column("Int", justify="right")
    table.add_column("HVC", justify="right")
    table.add_column("Reg", justify="right")
    table.add_column("Scl", justify="right")
    table.add_column("Lev", justify="right")
    table.add_column("Pen", justify="right")
    table.add_column("Score", justify="right", style="bold")
    table.add_column("Tier", justify="center")
    table.add_column("Stage", justify="center")

    tier_colors = {1: "bold green", 2: "green", 3: "yellow", 4: "dim"}

    for c, ws, t, tl in scored[:limit]:
        style = tier_colors.get(t, "")
        table.add_row(
            c.company_name, c.region,
            f"{c.score_integration:.0f}", f"{c.score_high_value_crop:.0f}",
            f"{c.score_registration_ease:.0f}", f"{c.score_scale_potential:.0f}",
            f"{c.score_strategic_leverage:.0f}", f"{c.penalty_complexity:.0f}",
            f"{ws:.2f}", tl, c.pipeline_stage,
            style=style,
        )

    console.print(table)
    if len(scored) > limit:
        console.print(f"[dim]Showing {limit} of {len(scored)}[/dim]")
