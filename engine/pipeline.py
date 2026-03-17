"""Pipeline stage management for Kelp Target Engine."""

from datetime import date

from engine.models import Company, PipelineEvent


STAGE_ORDER = ["L0", "L1", "L2", "L3", "L4", "L5"]


def advance_stage(company: Company, to_stage: str, note: str = "") -> str:
    """Move a company to a new pipeline stage.

    Returns the new stage. Raises ValueError if the stage is invalid.
    """
    if to_stage not in STAGE_ORDER:
        raise ValueError(f"Invalid stage: {to_stage}. Must be one of {STAGE_ORDER}")

    old_stage = company.pipeline_stage
    company.pipeline_stage = to_stage
    company.pipeline_history.append(PipelineEvent(
        stage=to_stage,
        date=date.today().isoformat(),
        note=note or f"Moved from {old_stage} to {to_stage}",
    ))
    company.touch()
    return to_stage


def get_pipeline_summary(companies: list[Company], config: dict) -> list[dict]:
    """Generate pipeline funnel summary.

    Returns a list of dicts, one per stage (L5 first), with:
      stage, stage_name, count, total_hectares, total_revenue, top_companies
    """
    from engine.revenue import calculate_revenue

    stage_names = config["pipeline_stages"]
    summary = []

    for stage in reversed(STAGE_ORDER):
        stage_companies = [c for c in companies if c.pipeline_stage == stage and not c.excluded]
        total_hectares = sum(c.hectares_controlled for c in stage_companies)
        revenues = [(c, calculate_revenue(c, config)) for c in stage_companies]
        total_revenue = sum(r for _, r in revenues)

        # Top 3 by revenue
        revenues.sort(key=lambda x: -x[1])
        top = [{"name": c.company_name, "revenue": r} for c, r in revenues[:3]]

        summary.append({
            "stage": stage,
            "stage_name": stage_names.get(stage, stage),
            "count": len(stage_companies),
            "total_hectares": total_hectares,
            "total_revenue": total_revenue,
            "top_companies": top,
        })

    return summary


def get_company_history(company: Company) -> list[PipelineEvent]:
    """Get the pipeline movement history for a company."""
    return company.pipeline_history
