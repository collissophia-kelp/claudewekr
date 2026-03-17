"""Terminal rendering of the target list grouped by pipeline stage."""

from rich.console import Console
from rich.table import Table

from engine.models import Company
from engine.scoring import score_company
from engine.revenue import calculate_revenue
from engine.pipeline import STAGE_ORDER

console = Console()


def render_target_list(companies: list[Company], config: dict,
                       min_stage: str = "L1") -> None:
    """Render the target list grouped by pipeline stage."""
    min_idx = STAGE_ORDER.index(min_stage)

    targets = []
    for c in companies:
        if c.excluded:
            continue
        stage_idx = STAGE_ORDER.index(c.pipeline_stage)
        if stage_idx >= min_idx:
            ws, t, tl = score_company(c, config)
            rev = calculate_revenue(c, config)
            targets.append((c, ws, t, tl, rev))

    stage_names = config["pipeline_stages"]

    for stage in reversed(STAGE_ORDER):
        if STAGE_ORDER.index(stage) < min_idx:
            continue

        stage_targets = [(c, ws, t, tl, rev) for c, ws, t, tl, rev in targets
                         if c.pipeline_stage == stage]
        if not stage_targets:
            continue

        stage_targets.sort(key=lambda x: (x[0].region, -x[1]))

        table = Table(title=f"{stage} \u2014 {stage_names.get(stage, '')} ({len(stage_targets)})")
        table.add_column("Company", style="bold", max_width=30)
        table.add_column("Region", max_width=18)
        table.add_column("Score", justify="right")
        table.add_column("Tier")
        table.add_column("Hectares", justify="right")
        table.add_column("Y5 Revenue", justify="right")
        table.add_column("Owner")

        subtotal_ha = 0.0
        subtotal_rev = 0.0

        for c, ws, t, tl, rev in stage_targets:
            table.add_row(
                c.company_name, c.region, f"{ws:.2f}", tl,
                f"{c.hectares_controlled:,.0f}", f"\u20ac{rev:,.0f}",
                c.pipeline_owner,
            )
            subtotal_ha += c.hectares_controlled
            subtotal_rev += rev

        table.add_row(
            "[bold]Subtotal[/bold]", "", "", "",
            f"[bold]{subtotal_ha:,.0f}[/bold]",
            f"[bold]\u20ac{subtotal_rev:,.0f}[/bold]", "",
        )

        console.print(table)
        console.print()
