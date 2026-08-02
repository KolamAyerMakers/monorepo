"""Progress service result models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from maker_guide.curriculum.models import Quest, SessionObjective
from maker_guide.repositories.course_release import CourseRelease
from maker_guide.repositories.helpers import JsonPayload
from maker_guide.repositories.quest_assignment import QuestAssignment
from maker_guide.repositories.quest_attempt import QuestAttempt
from maker_guide.repositories.quest_completion import QuestCompletion
from maker_guide.repositories.tier_promotion import TierPromotion

type QuestAttemptOutcome = Literal["passed", "failed"]


@dataclass(frozen=True, kw_only=True, slots=True)
class CourseReleaseInput:
    """Input for globally releasing a course session."""

    session_reached: str
    """Released session id from the Python curriculum catalog."""

    updated_at: str
    """ISO timestamp for when the course release changed."""

    source: str
    """Source that updated the course release."""


@dataclass(frozen=True, kw_only=True, slots=True)
class CourseReleaseResult:
    """Result of updating global course release state."""

    course_release: CourseRelease
    """Global course release row after the update."""

    changed: bool
    """Whether this call changed the course release."""


@dataclass(frozen=True, kw_only=True, slots=True)
class CurrentQuestResult:
    """Deterministic current quest selection result."""

    quest: Quest | None
    """Selected quest, absent while objectives remain or every available quest is complete."""

    assignment: QuestAssignment | None
    """Stored assignment for the selected quest."""

    assigned_now: bool
    """Whether the service created the assignment before returning it."""


@dataclass(frozen=True, kw_only=True, slots=True)
class CurrentSessionObjectiveResult:
    """Current-session objective or older backlog after current-session completion."""

    session_id: str
    objective: SessionObjective | None
    evidence_since: str


@dataclass(frozen=True, kw_only=True, slots=True)
class SessionObjectiveCompletionResult:
    """Result of completing a session objective."""

    score_total: int
    """Course score total after completion handling."""

    tier_promotions: tuple[TierPromotion, ...]
    """Tier promotions newly recorded by this completion."""


@dataclass(frozen=True, kw_only=True, slots=True)
class QuestAttemptResult:
    """Result of recording one deterministic quest validation attempt."""

    attempt: QuestAttempt
    """Recorded quest attempt with its SQLite id."""


@dataclass(frozen=True, kw_only=True, slots=True)
class QuestCompletionInput:
    """Input for completing a quest through the progress service."""

    handle: str
    """Learner handle."""

    quest_id: str
    """Quest id from the Python curriculum catalog."""

    attempt_id: int
    """Validation attempt id that must match and have passed."""

    completed_at: str
    """ISO timestamp for when the quest was completed."""

    source: str
    """Source that recorded completion."""


@dataclass(frozen=True, kw_only=True, slots=True)
class QuestCompletionResult:
    """Result of completing a quest through the progress service."""

    completion: QuestCompletion
    """Quest completion row."""

    completed_now: bool
    """Whether this call inserted the completion and side effects."""

    score_total: int
    """Course score total after completion handling."""

    tier_promotions: tuple[TierPromotion, ...]
    """Tier promotions newly recorded by this completion."""


@dataclass(frozen=True, kw_only=True, slots=True)
class QuestAttemptInput:
    """Input for recording a quest validation attempt."""

    handle: str
    """Learner handle."""

    quest_id: str
    """Quest id from the Python curriculum catalog."""

    attempted_at: str
    """ISO timestamp for when validation ran."""

    source: str
    """Source that requested validation."""

    outcome: QuestAttemptOutcome
    """Deterministic validation outcome."""

    evidence: JsonPayload
    """Validation facts used to decide the outcome."""

    failure_reason: str | None = None
    """Optional deterministic reason for validation failure."""


class ProgressServiceError(RuntimeError):
    """Raised when progress service preconditions are not met."""
