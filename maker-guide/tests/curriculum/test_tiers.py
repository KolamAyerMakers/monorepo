"""Tests for shared course tier resolution."""

from __future__ import annotations

from dataclasses import replace

import pytest

from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.curriculum.models import CourseCatalog, Tier
from maker_guide.curriculum.tiers import crossed_tiers, current_tier, current_tier_id


@pytest.mark.parametrize(
    ("score_total", "expected_tier_id"),
    [
        (0, None),
        (99, None),
        (100, "apprentice"),
        (249, "apprentice"),
        (250, "builder"),
        (9999, "builder"),
    ],
)
def test_current_tier_resolves_highest_reached_threshold(
    score_total: int,
    expected_tier_id: str | None,
) -> None:
    """Current tier is the highest threshold not above the score total."""
    resolved_tier = current_tier(
        _catalog_with_tiers(
            Tier(id="apprentice", minimum_score=100, title="Apprentice"),
            Tier(id="builder", minimum_score=250, title="Builder"),
        ),
        score_total,
    )

    assert (None if resolved_tier is None else resolved_tier.id) == expected_tier_id


def test_current_tier_returns_none_when_course_has_no_tiers() -> None:
    """Courses without tiers have no current tier at any score."""
    assert current_tier(_catalog_with_tiers(), 1000) is None


def test_current_tier_id_returns_none_when_no_threshold_qualifies() -> None:
    """The shared tier-id helper preserves absent-tier semantics."""
    assert (
        current_tier_id(
            _catalog_with_tiers(Tier(id="apprentice", minimum_score=100, title="Apprentice")),
            99,
        )
        is None
    )


def test_crossed_tiers_returns_thresholds_crossed_between_scores() -> None:
    """Tier crossings include exact upper thresholds and exclude the previous score."""
    assert [
        tier.id
        for tier in crossed_tiers(
            _catalog_with_tiers(
                Tier(id="newcomer", minimum_score=0, title="Newcomer"),
                Tier(id="apprentice", minimum_score=100, title="Apprentice"),
                Tier(id="builder", minimum_score=250, title="Builder"),
            ),
            100,
            250,
        )
    ] == ["builder"]


def _catalog_with_tiers(*tiers: Tier) -> CourseCatalog:
    return CourseCatalog(replace(CATALOG.course, tiers=tiers))
