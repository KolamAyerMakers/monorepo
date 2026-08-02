"""Enrollment service models."""

from __future__ import annotations

from dataclasses import dataclass

from maker_guide.repositories.cohort_membership import CohortMembership


@dataclass(frozen=True, kw_only=True, slots=True)
class EnrollmentInput:
    """Input for enrolling a learner in a course cohort."""

    handle: str
    """Learner handle."""

    course_id: str
    """Course id from the Python curriculum catalog."""

    joined_at: str
    """ISO timestamp for when the learner joined the course cohort."""

    source: str
    """Source that requested enrollment."""

    rank_eligible: bool = True
    """Whether the learner is eligible for cohort rankings."""


@dataclass(frozen=True, kw_only=True, slots=True)
class EnrollmentResult:
    """Result of enrolling a learner in a course cohort."""

    membership: CohortMembership
    """Cohort membership row after enrollment."""

    created: bool
    """Whether this call created the cohort membership row."""


class EnrollmentServiceError(RuntimeError):
    """Raised when enrollment preconditions are not met."""
