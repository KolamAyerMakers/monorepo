"""Tests for the application catalog composition root."""

from __future__ import annotations

from maker_guide.curriculum.catalogs import (
    DEFAULT_CATALOG,
    DEFAULT_COURSE,
    DEFAULT_COURSE_ID,
    catalog_by_course_id,
    course_by_id,
)
from maker_guide.curriculum.linux_foundations_2026_07 import LINUX_FOUNDATIONS_2026_07


def test_default_catalog_is_linux_foundations_july_2026() -> None:
    """The current deployment intentionally composes one course catalog."""
    assert DEFAULT_COURSE is LINUX_FOUNDATIONS_2026_07
    assert DEFAULT_COURSE_ID == "lf2607"
    assert DEFAULT_CATALOG.course is DEFAULT_COURSE


def test_catalog_lookup_returns_default_catalog_for_default_course_id() -> None:
    """Known course ids resolve through the composition root."""
    assert course_by_id(DEFAULT_COURSE_ID) is DEFAULT_COURSE
    assert catalog_by_course_id(DEFAULT_COURSE_ID) is DEFAULT_CATALOG


def test_catalog_lookup_returns_none_for_unknown_course_id() -> None:
    """Unknown course ids remain caller-owned policy decisions."""
    assert course_by_id("missing-course") is None
    assert catalog_by_course_id("missing-course") is None
