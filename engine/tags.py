"""Tag management and filtering for Kelp Target Engine."""

from collections import Counter

from engine.models import Company


def auto_generate_tags(company: Company) -> list[str]:
    """Auto-generate tags from company data (crops, region, business type)."""
    tags = set(company.tags)

    # Crop tags
    for crop in company.main_crops:
        tag = "crop:" + crop.lower().replace(" ", "_")
        tags.add(tag)

    # Region tag
    if company.region:
        tag = "region:" + company.region.lower().replace(" ", "_").replace("&", "and")
        tags.add(tag)

    # Exclusion tags from business type
    bt = company.business_type.lower()
    if "feed" in bt and "animal" in bt:
        tags.add("exclude:animal_feed")
    if "restaurant" in bt or "qsr" in bt:
        tags.add("exclude:restaurant")
    if "seed" in bt and "company" in bt:
        tags.add("exclude:seed")
    if "dairy" in bt:
        tags.add("exclude:dairy")
    if "aquaculture" in bt:
        tags.add("exclude:aquaculture")

    return sorted(tags)


def add_tag(company: Company, tag: str) -> None:
    """Add a tag to a company."""
    if tag not in company.tags:
        company.tags.append(tag)
        company.tags.sort()
        company.touch()


def remove_tag(company: Company, tag: str) -> bool:
    """Remove a tag from a company. Returns True if tag was found and removed."""
    if tag in company.tags:
        company.tags.remove(tag)
        company.touch()
        return True
    return False


def filter_by_tags(companies: list[Company], include_tags: list[str] | None = None,
                   exclude_tags: list[str] | None = None) -> list[Company]:
    """Filter companies by tags. Include = must have ALL. Exclude = must have NONE."""
    result = companies
    if include_tags:
        result = [c for c in result if all(t in c.tags for t in include_tags)]
    if exclude_tags:
        result = [c for c in result if not any(t in c.tags for t in exclude_tags)]
    return result


def filter_companies(companies: list[Company], config: dict,
                     tier: int | None = None,
                     region: str | None = None,
                     pipeline_stage: str | None = None,
                     min_stage: str | None = None,
                     tags: list[str] | None = None,
                     exclude_excluded: bool = False,
                     max_tier: int | None = None) -> list[Company]:
    """Filter companies by multiple criteria."""
    from engine.scoring import score_company

    stage_order = ["L0", "L1", "L2", "L3", "L4", "L5"]
    result = companies

    if exclude_excluded:
        result = [c for c in result if not c.excluded]

    if tier is not None:
        result = [c for c in result if score_company(c, config)[1] == tier]

    if max_tier is not None:
        result = [c for c in result if score_company(c, config)[1] <= max_tier]

    if region is not None:
        result = [c for c in result if c.region.lower() == region.lower()]

    if pipeline_stage is not None:
        result = [c for c in result if c.pipeline_stage == pipeline_stage]

    if min_stage is not None:
        min_idx = stage_order.index(min_stage)
        result = [c for c in result if stage_order.index(c.pipeline_stage) >= min_idx]

    if tags:
        result = filter_by_tags(result, include_tags=tags)

    return result


def count_tags(companies: list[Company]) -> dict[str, int]:
    """Count tag usage across all companies."""
    counter = Counter()
    for c in companies:
        counter.update(c.tags)
    return dict(counter.most_common())
