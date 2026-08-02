"""Application catalog composition root."""

from __future__ import annotations

from maker_guide.curriculum.linux_foundations_2026_07 import LINUX_FOUNDATIONS_2026_07
from maker_guide.curriculum.models import Course, CourseCatalog

DEFAULT_COURSE = LINUX_FOUNDATIONS_2026_07
DEFAULT_COURSE_ID = DEFAULT_COURSE.id
DEFAULT_CATALOG = CourseCatalog(DEFAULT_COURSE)
COURSES = (DEFAULT_COURSE,)
_COURSES_BY_ID = {course.id: course for course in COURSES}
_CATALOGS_BY_COURSE_ID = {DEFAULT_COURSE_ID: DEFAULT_CATALOG}


def course_by_id(course_id: str) -> Course | None:
    """Return the composed course for a known course id."""
    return _COURSES_BY_ID.get(course_id)


def catalog_by_course_id(course_id: str) -> CourseCatalog | None:
    """Return the composed catalog for a known course id."""
    return _CATALOGS_BY_COURSE_ID.get(course_id)
