"""Shared course tier resolution helpers."""

from __future__ import annotations

from maker_guide.curriculum.models import CourseCatalog, Tier


def current_tier(catalog: CourseCatalog, score_total: int) -> Tier | None:
    """Return the highest tier whose threshold is not above the score total."""
    resolved_tier: Tier | None = None
    for tier in catalog.course.tiers:
        if tier.minimum_score <= score_total:
            resolved_tier = tier
    return resolved_tier


def current_tier_id(catalog: CourseCatalog, score_total: int) -> str | None:
    """Return the current tier id, or none when no threshold qualifies."""
    tier = current_tier(catalog, score_total)
    if tier is None:
        return None
    return tier.id


def crossed_tiers(
    catalog: CourseCatalog,
    previous_score_total: int,
    score_total: int,
) -> tuple[Tier, ...]:
    """Return tiers crossed between two score totals in catalog order."""
    return tuple(
        tier
        for tier in catalog.course.tiers
        if previous_score_total < tier.minimum_score <= score_total
    )
