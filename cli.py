#!/usr/bin/env python3
"""Kelp Target Engine — Strategic Partnership Target Management CLI."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from engine.config import load_config, save_config, load_scoring_guide
from engine.models import Company, load_companies, save_companies, DEFAULT_COMPANIES_PATH
from engine.scoring import score_company, score_all, what_if, audit_companies
from engine.revenue import calculate_revenue, revenue_scenario
from engine.tags import auto_generate_tags, add_tag, remove_tag, filter_companies, count_tags
from engine.pipeline import advance_stage, get_pipeline_summary, get_company_history, STAGE_ORDER

console = Console()
DATA_DIR = Path(__file__).parent / "data"
CONFIG_PATH = DATA_DIR / "config.json"
COMPANIES_PATH = DEFAULT_COMPANIES_PATH


def _load():
    """Load config and companies."""
    config = load_config(CONFIG_PATH)
    companies = load_companies(COMPANIES_PATH)
    return config, companies


def _save(companies):
    """Save companies."""
    save_companies(companies, COMPANIES_PATH)


def _find_company(companies, name):
    """Find a company by name (case-insensitive partial match)."""
    name_lower = name.lower()
    # Exact match first
    for c in companies:
        if c.company_name.lower() == name_lower:
            return c
    # Partial match
    matches = [c for c in companies if name_lower in c.company_name.lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        console.print(f"[yellow]Multiple matches for '{name}':[/yellow]")
        for m in matches:
            console.print(f"  - {m.company_name}")
        return None
    console.print(f"[red]Company '{name}' not found.[/red]")
    return None


@click.group()
def cli():
    """Kelp Target Engine — Strategic Partnership Target Management."""
    pass


# ── Company Management ──────────────────────────────────────────────


@cli.command()
def add():
    """Add a new company interactively."""
    config, companies = _load()

    console.print("\n[bold]Add New Company[/bold]\n")

    name = click.prompt("Company name")
    # Check for duplicate
    if any(c.company_name.lower() == name.lower() for c in companies):
        console.print(f"[red]Company '{name}' already exists.[/red]")
        return

    hq = click.prompt("HQ Country", default="")
    region = click.prompt("Region", default="")
    btype = click.prompt("Business type", default="")
    countries = click.prompt("Countries with farms", default="")
    crops_str = click.prompt("Main crops (comma-separated)", default="")
    main_crops = [c.strip() for c in crops_str.split(",") if c.strip()]

    console.print("\n[bold]Scores (0-5):[/bold]")
    integration = click.prompt("  Integration", type=float, default=0.0)
    hvc = click.prompt("  High-Value Crop Exposure", type=float, default=0.0)
    reg = click.prompt("  Registration Ease", type=float, default=0.0)
    scale = click.prompt("  Scale Potential", type=float, default=0.0)
    leverage = click.prompt("  Strategic Leverage", type=float, default=0.0)
    penalty = click.prompt("  Penalty Complexity (0 to -2)", type=float, default=0.0)

    hectares = click.prompt("Hectares controlled", type=float, default=0.0)
    stage = click.prompt("Pipeline stage", type=click.Choice(STAGE_ORDER), default="L0")
    owner = click.prompt("Owner", default="")
    tags_str = click.prompt("Tags (comma-separated)", default="")
    manual_tags = [t.strip() for t in tags_str.split(",") if t.strip()]
    notes = click.prompt("Notes", default="")

    company = Company(
        company_name=name,
        hq_country=hq,
        region=region,
        business_type=btype,
        countries_with_controlled_farms=countries,
        main_crops=main_crops,
        score_integration=integration,
        score_high_value_crop=hvc,
        score_registration_ease=reg,
        score_scale_potential=scale,
        score_strategic_leverage=leverage,
        penalty_complexity=penalty,
        hectares_controlled=hectares,
        pipeline_stage=stage,
        pipeline_owner=owner,
        tags=manual_tags,
        notes=notes,
    )
    company.tags = auto_generate_tags(company)

    ws, tier, tl = score_company(company, config)
    rev = calculate_revenue(company, config)

    console.print(f"\n[green]Weighted Score: {ws} ({tl})[/green]")
    console.print(f"[green]Year 5 Revenue: \u20ac{rev:,.0f}[/green]")

    companies.append(company)
    _save(companies)
    console.print(f"\n[bold green]Saved '{name}' to companies.json[/bold green]")


@cli.command()
@click.argument("name")
def edit(name):
    """Edit an existing company by name."""
    config, companies = _load()
    company = _find_company(companies, name)
    if not company:
        return

    console.print(f"\n[bold]Editing: {company.company_name}[/bold]")
    console.print("Press Enter to keep current value.\n")

    fields = [
        ("hq_country", "HQ Country"),
        ("region", "Region"),
        ("business_type", "Business type"),
        ("countries_with_controlled_farms", "Countries with farms"),
        ("notes", "Notes"),
        ("pipeline_owner", "Owner"),
    ]
    for field, label in fields:
        current = getattr(company, field)
        new_val = click.prompt(f"  {label}", default=current)
        setattr(company, field, new_val)

    crops_str = click.prompt("  Main crops (comma-separated)",
                             default=", ".join(company.main_crops))
    company.main_crops = [c.strip() for c in crops_str.split(",") if c.strip()]

    score_fields = [
        ("score_integration", "Integration"),
        ("score_high_value_crop", "High-Value Crop"),
        ("score_registration_ease", "Registration Ease"),
        ("score_scale_potential", "Scale Potential"),
        ("score_strategic_leverage", "Strategic Leverage"),
        ("penalty_complexity", "Penalty Complexity"),
    ]
    console.print("\n[bold]Scores:[/bold]")
    for field, label in score_fields:
        current = getattr(company, field)
        new_val = click.prompt(f"  {label}", type=float, default=current)
        setattr(company, field, new_val)

    company.hectares_controlled = click.prompt("  Hectares", type=float,
                                               default=company.hectares_controlled)
    company.pipeline_stage = click.prompt("  Pipeline stage",
                                          type=click.Choice(STAGE_ORDER),
                                          default=company.pipeline_stage)

    company.tags = auto_generate_tags(company)
    company.touch()

    ws, tier, tl = score_company(company, config)
    rev = calculate_revenue(company, config)
    console.print(f"\n[green]Updated: {ws} ({tl}), Revenue: \u20ac{rev:,.0f}[/green]")

    _save(companies)


@cli.command()
@click.argument("name")
@click.option("--reason", "-r", prompt="Exclusion reason", help="Reason for exclusion")
def remove(name, reason):
    """Soft-delete a company (set excluded=true)."""
    config, companies = _load()
    company = _find_company(companies, name)
    if not company:
        return

    company.excluded = True
    company.exclusion_reason = reason
    company.touch()
    _save(companies)
    console.print(f"[yellow]'{company.company_name}' excluded: {reason}[/yellow]")


# ── Viewing & Filtering ─────────────────────────────────────────────


@cli.command(name="list")
@click.option("--tier", type=int, help="Filter by tier (1-4)")
@click.option("--region", type=str, help="Filter by region")
@click.option("--stage", type=str, help="Filter by pipeline stage")
@click.option("--tag", multiple=True, help="Filter by tag (can specify multiple)")
@click.option("--min-stage", type=str, help="Minimum pipeline stage (e.g. L2)")
@click.option("--show-excluded", is_flag=True, help="Include excluded companies")
@click.option("--sort", "sort_by", type=click.Choice(["score", "name", "revenue", "tier"]),
              default="score", help="Sort order")
@click.option("--limit", type=int, default=50, help="Max rows to display")
def list_companies(tier, region, stage, tag, min_stage, show_excluded, sort_by, limit):
    """List companies with optional filters."""
    config, companies = _load()

    filtered = filter_companies(
        companies, config,
        tier=tier, region=region, pipeline_stage=stage,
        min_stage=min_stage, tags=list(tag) if tag else None,
        exclude_excluded=not show_excluded,
    )

    # Score and sort
    scored = [(c, *score_company(c, config)) for c in filtered]

    if sort_by == "score":
        scored.sort(key=lambda x: -x[1])
    elif sort_by == "name":
        scored.sort(key=lambda x: x[0].company_name.lower())
    elif sort_by == "revenue":
        scored.sort(key=lambda x: -calculate_revenue(x[0], config))
    elif sort_by == "tier":
        scored.sort(key=lambda x: (x[2], -x[1]))

    table = Table(title=f"Companies ({len(scored)} results)")
    table.add_column("Company", style="bold", max_width=35)
    table.add_column("Region", max_width=20)
    table.add_column("Score", justify="right")
    table.add_column("Tier", justify="center")
    table.add_column("Stage", justify="center")
    table.add_column("Hectares", justify="right")
    table.add_column("Y5 Revenue", justify="right")

    tier_colors = {1: "bold green", 2: "green", 3: "yellow", 4: "dim"}

    for c, ws, t, tl in scored[:limit]:
        rev = calculate_revenue(c, config)
        style = tier_colors.get(t, "")
        table.add_row(
            c.company_name,
            c.region,
            f"{ws:.2f}",
            tl,
            c.pipeline_stage,
            f"{c.hectares_controlled:,.0f}",
            f"\u20ac{rev:,.0f}",
            style=style,
        )

    console.print(table)
    if len(scored) > limit:
        console.print(f"[dim]Showing {limit} of {len(scored)} results. Use --limit to show more.[/dim]")


@cli.command()
@click.argument("name")
def view(name):
    """View detailed information for a single company."""
    config, companies = _load()
    company = _find_company(companies, name)
    if not company:
        return

    ws, tier, tl = score_company(company, config)
    rev = calculate_revenue(company, config)

    panel_content = f"""[bold]{company.company_name}[/bold]
HQ: {company.hq_country} | Region: {company.region}
Type: {company.business_type}
Farm Countries: {company.countries_with_controlled_farms}
Main Crops: {', '.join(company.main_crops)}

[bold]Scores:[/bold]
  Integration:        {company.score_integration}
  High-Value Crop:    {company.score_high_value_crop}
  Registration Ease:  {company.score_registration_ease}
  Scale Potential:    {company.score_scale_potential}
  Strategic Leverage: {company.score_strategic_leverage}
  Penalty Complexity: {company.penalty_complexity}
  [bold]Weighted Score:     {ws:.2f} ({tl})[/bold]

[bold]Pipeline:[/bold] {company.pipeline_stage} | Owner: {company.pipeline_owner}
[bold]Hectares:[/bold] {company.hectares_controlled:,.0f}
[bold]Year 5 Revenue:[/bold] \u20ac{rev:,.0f}

[bold]Tags:[/bold] {', '.join(company.tags) or 'None'}
[bold]Notes:[/bold] {company.notes or 'None'}

Added: {company.date_added} | Updated: {company.date_last_updated}"""

    if company.excluded:
        panel_content += f"\n[red]EXCLUDED: {company.exclusion_reason}[/red]"

    console.print(Panel(panel_content, title=company.company_name, border_style="blue"))


@cli.command()
@click.argument("query")
def search(query):
    """Search companies by name, crop, country, or tag."""
    config, companies = _load()
    query_lower = query.lower()

    matches = []
    for c in companies:
        if (query_lower in c.company_name.lower()
            or query_lower in c.hq_country.lower()
            or query_lower in c.region.lower()
            or query_lower in c.business_type.lower()
            or any(query_lower in crop.lower() for crop in c.main_crops)
            or any(query_lower in tag.lower() for tag in c.tags)
            or query_lower in c.countries_with_controlled_farms.lower()):
            matches.append(c)

    if not matches:
        console.print(f"[yellow]No matches for '{query}'[/yellow]")
        return

    table = Table(title=f"Search: '{query}' ({len(matches)} results)")
    table.add_column("Company", style="bold")
    table.add_column("Region")
    table.add_column("Score", justify="right")
    table.add_column("Tier")
    table.add_column("Stage")

    for c in matches:
        ws, t, tl = score_company(c, config)
        table.add_row(c.company_name, c.region, f"{ws:.2f}", tl, c.pipeline_stage)

    console.print(table)


@cli.command()
def summary():
    """Dashboard: counts by tier, region, and pipeline stage."""
    config, companies = _load()
    active = [c for c in companies if not c.excluded]

    if not active:
        console.print("[yellow]No companies loaded. Use 'add' or 'import-xlsx' first.[/yellow]")
        return

    # Tier summary
    tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    tier_revenue = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
    for c in active:
        ws, t, _ = score_company(c, config)
        tier_counts[t] = tier_counts.get(t, 0) + 1
        tier_revenue[t] = tier_revenue.get(t, 0) + calculate_revenue(c, config)

    table = Table(title="Summary by Tier")
    table.add_column("Tier")
    table.add_column("Count", justify="right")
    table.add_column("Total Y5 Revenue", justify="right")
    for t in [1, 2, 3, 4]:
        table.add_row(f"Tier {t}", str(tier_counts[t]), f"\u20ac{tier_revenue[t]:,.0f}")
    table.add_row("[bold]Total[/bold]", f"[bold]{sum(tier_counts.values())}[/bold]",
                  f"[bold]\u20ac{sum(tier_revenue.values()):,.0f}[/bold]")
    console.print(table)

    # Region summary
    region_counts: dict[str, int] = {}
    for c in active:
        r = c.region or "Unknown"
        region_counts[r] = region_counts.get(r, 0) + 1

    table2 = Table(title="By Region")
    table2.add_column("Region")
    table2.add_column("Count", justify="right")
    for r, count in sorted(region_counts.items(), key=lambda x: -x[1]):
        table2.add_row(r, str(count))
    console.print(table2)

    # Pipeline summary
    stage_counts: dict[str, int] = {}
    for c in active:
        stage_counts[c.pipeline_stage] = stage_counts.get(c.pipeline_stage, 0) + 1

    table3 = Table(title="By Pipeline Stage")
    table3.add_column("Stage")
    table3.add_column("Name")
    table3.add_column("Count", justify="right")
    stage_names = config["pipeline_stages"]
    for s in STAGE_ORDER:
        table3.add_row(s, stage_names.get(s, ""), str(stage_counts.get(s, 0)))
    console.print(table3)

    console.print(f"\n[bold]Total active companies: {len(active)}[/bold]")
    console.print(f"[dim]Excluded: {len(companies) - len(active)}[/dim]")


# ── Scoring ──────────────────────────────────────────────────────────


@cli.command()
def rescore():
    """Recalculate all weighted scores and tiers (display only — scores are always computed on read)."""
    config, companies = _load()
    active = [c for c in companies if not c.excluded]
    scored = score_all(active, config)
    scored.sort(key=lambda x: -x[1])

    table = Table(title="All Companies — Rescored")
    table.add_column("Company", style="bold")
    table.add_column("Score", justify="right")
    table.add_column("Tier")

    for c, ws, t, tl in scored[:50]:
        table.add_row(c.company_name, f"{ws:.2f}", tl)

    console.print(table)
    console.print(f"[dim]Showing top 50 of {len(scored)}. Scores are always computed fresh from raw data.[/dim]")


@cli.command(name="what-if")
@click.option("--weight", "-w", multiple=True,
              help="Weight override in format key=value (e.g. integration=0.40)")
def what_if_cmd(weight):
    """Simulate weight changes and see which companies change tier."""
    config, companies = _load()
    active = [c for c in companies if not c.excluded]

    if not weight:
        console.print("[red]Specify at least one --weight override (e.g. --weight integration=0.40)[/red]")
        return

    overrides = {}
    for w in weight:
        if "=" not in w:
            console.print(f"[red]Invalid format: '{w}'. Use key=value.[/red]")
            return
        key, val = w.split("=", 1)
        overrides[key.strip()] = float(val.strip())

    changes = what_if(active, config, overrides)

    if not changes:
        console.print("[green]No tier changes under proposed weights.[/green]")
        return

    console.print(f"\n[bold]Comparing current vs proposed weights:[/bold]")
    for k, v in overrides.items():
        current = config["scoring_weights"].get(k, "?")
        console.print(f"  {k}: {current} -> {v}")

    table = Table(title=f"Companies Changing Tier ({len(changes)})")
    table.add_column("Direction")
    table.add_column("Company", style="bold")
    table.add_column("Old Score", justify="right")
    table.add_column("New Score", justify="right")
    table.add_column("Old Tier")
    table.add_column("New Tier")

    for ch in changes:
        arrow = "[green]\u2191[/green]" if ch["direction"] == "up" else "[red]\u2193[/red]"
        table.add_row(
            arrow,
            ch["company_name"],
            f"{ch['old_score']:.2f}",
            f"{ch['new_score']:.2f}",
            f"Tier {ch['old_tier']}",
            f"Tier {ch['new_tier']}",
        )

    console.print(table)

    # Summary counts
    current_tiers = {1: 0, 2: 0, 3: 0, 4: 0}
    new_tiers = {1: 0, 2: 0, 3: 0, 4: 0}
    from engine.scoring import calculate_weighted_score, assign_tier
    new_weights = {**config["scoring_weights"], **overrides}
    for c in active:
        old_ws = calculate_weighted_score(c, config["scoring_weights"])
        new_ws = calculate_weighted_score(c, new_weights)
        old_t = assign_tier(old_ws, config["tier_thresholds"])
        new_t = assign_tier(new_ws, config["tier_thresholds"])
        current_tiers[old_t] += 1
        new_tiers[new_t] += 1

    console.print("\n[bold]Tier Counts:[/bold]")
    for t in [1, 2, 3, 4]:
        delta = new_tiers[t] - current_tiers[t]
        delta_str = f" ({'+' if delta > 0 else ''}{delta})" if delta != 0 else ""
        console.print(f"  Tier {t}: {current_tiers[t]} -> {new_tiers[t]}{delta_str}")


@cli.command()
def audit():
    """Flag companies with missing scores or data gaps."""
    config, companies = _load()
    issues = audit_companies(companies)

    if not issues:
        console.print("[green]No data quality issues found.[/green]")
        return

    table = Table(title=f"Data Quality Issues ({len(issues)} companies)")
    table.add_column("Company", style="bold")
    table.add_column("Issues")

    for item in issues:
        table.add_row(item["company_name"], "; ".join(item["issues"]))

    console.print(table)


# ── Pipeline ─────────────────────────────────────────────────────────


@cli.command()
@click.argument("name")
@click.option("--to", "to_stage", required=True, type=click.Choice(STAGE_ORDER),
              help="Target pipeline stage")
@click.option("--note", "-n", default="", help="Note for this transition")
def advance(name, to_stage, note):
    """Move a company to a new pipeline stage."""
    config, companies = _load()
    company = _find_company(companies, name)
    if not company:
        return

    old_stage = company.pipeline_stage
    advance_stage(company, to_stage, note)
    _save(companies)
    console.print(f"[green]{company.company_name}: {old_stage} -> {to_stage}[/green]")


@cli.command(name="pipeline")
def pipeline_cmd():
    """Show pipeline funnel (count + revenue per stage)."""
    config, companies = _load()
    funnel = get_pipeline_summary(companies, config)

    table = Table(title="Pipeline Funnel")
    table.add_column("Stage")
    table.add_column("Name")
    table.add_column("Count", justify="right")
    table.add_column("Hectares", justify="right")
    table.add_column("Y5 Revenue", justify="right")
    table.add_column("Key Companies")

    total_count = 0
    total_hectares = 0.0
    total_revenue = 0.0

    for s in funnel:
        top_names = ", ".join(t["name"] for t in s["top_companies"])
        table.add_row(
            s["stage"],
            s["stage_name"],
            str(s["count"]),
            f"{s['total_hectares']:,.0f}",
            f"\u20ac{s['total_revenue']:,.0f}",
            top_names,
        )
        total_count += s["count"]
        total_hectares += s["total_hectares"]
        total_revenue += s["total_revenue"]

    table.add_row(
        "[bold]TOTAL[/bold]", "", f"[bold]{total_count}[/bold]",
        f"[bold]{total_hectares:,.0f}[/bold]",
        f"[bold]\u20ac{total_revenue:,.0f}[/bold]", "",
    )
    console.print(table)


@cli.command()
@click.argument("name")
def history(name):
    """Show pipeline movement history for a company."""
    config, companies = _load()
    company = _find_company(companies, name)
    if not company:
        return

    events = get_company_history(company)
    if not events:
        console.print(f"[yellow]No pipeline history for '{company.company_name}'[/yellow]")
        return

    table = Table(title=f"Pipeline History: {company.company_name}")
    table.add_column("Date")
    table.add_column("Stage")
    table.add_column("Note")

    for e in events:
        table.add_row(e.date, e.stage, e.note)

    console.print(table)
    console.print(f"Current stage: [bold]{company.pipeline_stage}[/bold]")


# ── Revenue ──────────────────────────────────────────────────────────


@cli.command(name="revenue")
@click.option("--tier", type=int, help="Filter by tier")
@click.option("--region", type=str, help="Filter by region")
@click.option("--stage", type=str, help="Filter by pipeline stage")
@click.option("--tag", multiple=True, help="Filter by tag")
@click.option("--min-stage", type=str, help="Minimum pipeline stage")
def revenue_cmd(tier, region, stage, tag, min_stage):
    """Show revenue projections with optional filters."""
    config, companies = _load()

    filtered = filter_companies(
        companies, config,
        tier=tier, region=region, pipeline_stage=stage,
        min_stage=min_stage, tags=list(tag) if tag else None,
        exclude_excluded=True,
    )

    results = []
    for c in filtered:
        ws, t, tl = score_company(c, config)
        rev = calculate_revenue(c, config)
        results.append((c, ws, t, tl, rev))

    results.sort(key=lambda x: -x[4])

    table = Table(title=f"Revenue Projections ({len(results)} companies)")
    table.add_column("Company", style="bold", max_width=35)
    table.add_column("Tier")
    table.add_column("Stage")
    table.add_column("Hectares", justify="right")
    table.add_column("Y5 Revenue", justify="right")

    total_rev = 0.0
    total_ha = 0.0
    for c, ws, t, tl, rev in results:
        table.add_row(
            c.company_name, tl, c.pipeline_stage,
            f"{c.hectares_controlled:,.0f}", f"\u20ac{rev:,.0f}",
        )
        total_rev += rev
        total_ha += c.hectares_controlled

    table.add_row("[bold]TOTAL[/bold]", "", "", f"[bold]{total_ha:,.0f}[/bold]",
                  f"[bold]\u20ac{total_rev:,.0f}[/bold]")
    console.print(table)


@cli.command()
@click.option("--override", "-o", multiple=True,
              help="Assumption override in format key=value (e.g. price_per_litre_eur=10)")
def scenario(override):
    """Model revenue scenarios with modified assumptions."""
    config, companies = _load()
    active = [c for c in companies if not c.excluded]

    if not override:
        console.print("[red]Specify at least one --override (e.g. --override price_per_litre_eur=10)[/red]")
        return

    overrides = {}
    for o in override:
        if "=" not in o:
            console.print(f"[red]Invalid format: '{o}'. Use key=value.[/red]")
            return
        key, val = o.split("=", 1)
        overrides[key.strip()] = float(val.strip())

    console.print("[bold]Scenario Assumptions:[/bold]")
    for k, v in overrides.items():
        current = config["revenue_assumptions"].get(k, "?")
        console.print(f"  {k}: {current} -> {v}")

    results = revenue_scenario(active, config, overrides)

    table = Table(title="Revenue Scenario Impact")
    table.add_column("Company", style="bold")
    table.add_column("Current", justify="right")
    table.add_column("Scenario", justify="right")
    table.add_column("Delta", justify="right")
    table.add_column("%", justify="right")

    total_current = 0.0
    total_scenario = 0.0
    for r in results[:30]:
        table.add_row(
            r["company_name"],
            f"\u20ac{r['current_revenue']:,.0f}",
            f"\u20ac{r['scenario_revenue']:,.0f}",
            f"\u20ac{r['delta']:,.0f}",
            f"{r['delta_pct']:.1f}%",
        )
        total_current += r["current_revenue"]
        total_scenario += r["scenario_revenue"]

    total_delta = total_scenario - total_current
    total_pct = (total_delta / total_current * 100) if total_current > 0 else 0
    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]\u20ac{total_current:,.0f}[/bold]",
        f"[bold]\u20ac{total_scenario:,.0f}[/bold]",
        f"[bold]\u20ac{total_delta:,.0f}[/bold]",
        f"[bold]{total_pct:.1f}%[/bold]",
    )
    console.print(table)


# ── Export ───────────────────────────────────────────────────────────


@cli.command()
@click.option("--output", "-o", default="target_list.xlsx", help="Output file path")
@click.option("--min-stage", type=str, help="Minimum pipeline stage for target list")
def export(output, min_stage):
    """Generate a board-ready Excel workbook."""
    from data_io.excel_export import export_workbook

    config, companies = _load()
    export_workbook(companies, config, output, min_stage=min_stage)
    console.print(f"[bold green]Exported to {output}[/bold green]")


@cli.command(name="export-docx")
@click.option("--output", "-o", default="target_list.docx", help="Output file path")
def export_docx(output):
    """Generate a board-ready Word document."""
    from data_io.word_export import export_docx as _export_docx

    config, companies = _load()
    _export_docx(companies, config, output)
    console.print(f"[bold green]Exported to {output}[/bold green]")


# ── Import ───────────────────────────────────────────────────────────


@cli.command(name="import-xlsx")
@click.option("--file", "-f", "file_path", required=True, help="Path to Excel workbook")
@click.option("--merge", is_flag=True, help="Merge with existing data instead of replacing")
def import_xlsx_cmd(file_path, merge):
    """Import companies from an existing Excel workbook."""
    from data_io.excel_import import import_xlsx

    config, existing = _load()

    console.print(f"[bold]Importing from {file_path}...[/bold]")
    new_companies, warnings = import_xlsx(file_path, config)

    if merge and existing:
        existing_names = {c.company_name.lower() for c in existing}
        added = 0
        for c in new_companies:
            if c.company_name.lower() not in existing_names:
                existing.append(c)
                added += 1
        console.print(f"[green]Merged {added} new companies (skipped {len(new_companies) - added} duplicates)[/green]")
        _save(existing)
    else:
        _save(new_companies)
        console.print(f"[green]Imported {len(new_companies)} companies[/green]")

    save_config(config, CONFIG_PATH)

    if warnings:
        console.print(f"\n[yellow]Warnings ({len(warnings)}):[/yellow]")
        for w in warnings[:20]:
            console.print(f"  [yellow]- {w}[/yellow]")
        if len(warnings) > 20:
            console.print(f"  [dim]...and {len(warnings) - 20} more[/dim]")

    console.print(f"\n[bold]Run 'python cli.py audit' to review data quality.[/bold]")


@cli.command(name="import-csv")
@click.option("--file", "-f", "file_path", required=True, help="Path to CSV file")
@click.option("--merge", is_flag=True, help="Merge with existing data instead of replacing")
def import_csv_cmd(file_path, merge):
    """Bulk import companies from a CSV file."""
    from data_io.csv_import import import_csv

    config, existing = _load()

    console.print(f"[bold]Importing from {file_path}...[/bold]")
    new_companies, warnings = import_csv(file_path)

    if merge and existing:
        existing_names = {c.company_name.lower() for c in existing}
        added = 0
        for c in new_companies:
            if c.company_name.lower() not in existing_names:
                existing.append(c)
                added += 1
        console.print(f"[green]Merged {added} new companies[/green]")
        _save(existing)
    else:
        _save(new_companies)
        console.print(f"[green]Imported {len(new_companies)} companies[/green]")

    if warnings:
        console.print(f"\n[yellow]Warnings ({len(warnings)}):[/yellow]")
        for w in warnings:
            console.print(f"  [yellow]- {w}[/yellow]")


# ── Tags ─────────────────────────────────────────────────────────────


@cli.command(name="tag")
@click.argument("name")
@click.option("--add", "-a", "add_tags", multiple=True, help="Tags to add")
@click.option("--remove", "-r", "remove_tags", multiple=True, help="Tags to remove")
def tag_cmd(name, add_tags, remove_tags):
    """Add or remove tags on a company."""
    config, companies = _load()
    company = _find_company(companies, name)
    if not company:
        return

    for t in add_tags:
        add_tag(company, t)
        console.print(f"[green]Added tag: {t}[/green]")
    for t in remove_tags:
        if remove_tag(company, t):
            console.print(f"[yellow]Removed tag: {t}[/yellow]")
        else:
            console.print(f"[red]Tag not found: {t}[/red]")

    _save(companies)
    console.print(f"Tags: {', '.join(company.tags)}")


@cli.command(name="tags")
def tags_cmd():
    """List all tags in use with counts."""
    config, companies = _load()
    tag_counts = count_tags(companies)

    if not tag_counts:
        console.print("[yellow]No tags found.[/yellow]")
        return

    table = Table(title="Tags in Use")
    table.add_column("Tag")
    table.add_column("Count", justify="right")

    for tag, count in tag_counts.items():
        table.add_row(tag, str(count))

    console.print(table)


# ── Config ───────────────────────────────────────────────────────────


@cli.command(name="config")
@click.option("--set", "set_value", help="Set a config value: section.key=value")
def config_cmd(set_value):
    """View or update configuration."""
    config = load_config(CONFIG_PATH)

    if set_value:
        if "=" not in set_value or "." not in set_value.split("=")[0]:
            console.print("[red]Format: --set section.key=value (e.g. scoring_weights.integration=0.40)[/red]")
            return
        path, val = set_value.split("=", 1)
        section, key = path.split(".", 1)
        try:
            value = float(val)
        except ValueError:
            value = val

        from engine.config import update_config_value
        config = update_config_value(config, section, key, value)
        save_config(config, CONFIG_PATH)
        console.print(f"[green]Updated {section}.{key} = {value}[/green]")
        return

    # Display current config
    console.print(Panel("[bold]Scoring Weights[/bold]"))
    for k, v in config["scoring_weights"].items():
        console.print(f"  {k}: {v}")

    console.print(Panel("[bold]Tier Thresholds[/bold]"))
    for k, v in config["tier_thresholds"].items():
        console.print(f"  {k}: {v}")

    console.print(Panel("[bold]Revenue Assumptions[/bold]"))
    for k, v in config["revenue_assumptions"].items():
        console.print(f"  {k}: {v}")


if __name__ == "__main__":
    cli()
