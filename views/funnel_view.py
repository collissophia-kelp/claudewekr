"""Terminal rendering of the pipeline funnel."""

from rich.console import Console
from rich.table import Table

from engine.models import Company
from engine.pipeline import get_pipeline_summary

console = Console()


def render_funnel(companies: list[Company], config: dict) -> None:
    """Render the pipeline funnel as a rich table."""
    funnel = get_pipeline_summary(companies, config)

    table = Table(title="Pipeline Funnel")
    table.add_column("Stage", style="bold")
    table.add_column("Name")
    table.add_column("Count", justify="right")
    table.add_column("Hectares", justify="right")
    table.add_column("Y5 Revenue", justify="right")
    table.add_column("Key Companies", max_width=40)

    total_count = 0
    total_ha = 0.0
    total_rev = 0.0

    for s in funnel:
        top = ", ".join(t["name"] for t in s["top_companies"])
        table.add_row(
            s["stage"], s["stage_name"],
            str(s["count"]),
            f"{s['total_hectares']:,.0f}",
            f"\u20ac{s['total_revenue']:,.0f}",
            top,
        )
        total_count += s["count"]
        total_ha += s["total_hectares"]
        total_rev += s["total_revenue"]

    table.add_row(
        "[bold]TOTAL[/bold]", "",
        f"[bold]{total_count}[/bold]",
        f"[bold]{total_ha:,.0f}[/bold]",
        f"[bold]\u20ac{total_rev:,.0f}[/bold]",
        "",
    )

    console.print(table)
