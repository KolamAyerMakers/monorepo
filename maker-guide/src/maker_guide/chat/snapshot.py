"""Read-only learner snapshot queries for chat."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from maker_guide.curriculum.models import CourseCatalog
from maker_guide.curriculum.tiers import current_tier_id
from maker_guide.repositories.cohort_membership import get_membership
from maker_guide.repositories.course_release import get_course_release
from maker_guide.repositories.help_interaction import list_recent_help_interactions
from maker_guide.repositories.quest_assignment import list_assignments
from maker_guide.repositories.quest_completion import list_completed_quest_ids
from maker_guide.repositories.score_ledger import total_score_for_course


@dataclass(frozen=True, kw_only=True, slots=True)
class LearnerSnapshot:
    """Curated learner state for deterministic chat handling."""

    handle: str
    """Resolved learner handle."""
    course_id: str
    """Course id from the Python curriculum catalog."""
    current_session: str | None
    """Latest reached session id, if known."""
    taught_commands: tuple[str, ...]
    """Commands introduced through the current reached session."""
    taught_skills: tuple[str, ...]
    """Skills introduced through the current reached session."""
    pending_quests: tuple[str, ...]
    """Assigned incomplete quests plus the next available unassigned quest."""
    completed_quests: tuple[str, ...]
    """Completed quest ids in catalog order."""
    score: int
    """Derived course score total."""
    tier: str | None
    """Current symbolic tier id, if any."""
    recent_help_topics: tuple[str, ...]
    """Recent help topic tags from recorded interactions."""


def build_learner_snapshot(
    database_connection: sqlite3.Connection,
    catalog: CourseCatalog,
    handle: str,
) -> LearnerSnapshot:
    """Build a deterministic learner snapshot from catalog and SQLite state."""
    membership = get_membership(database_connection, handle, catalog.course.id)
    course_release = get_course_release(database_connection, catalog.course.id)
    if membership is None or course_release is None:
        return LearnerSnapshot(
            handle=handle,
            course_id=catalog.course.id,
            current_session=None if course_release is None else course_release.session_reached,
            taught_commands=(),
            taught_skills=(),
            pending_quests=(),
            completed_quests=(),
            score=0,
            tier=current_tier_id(catalog, 0),
            recent_help_topics=_recent_help_topics(database_connection, handle),
        )

    completed_quest_ids = list_completed_quest_ids(database_connection, handle, catalog.course.id)
    score = total_score_for_course(database_connection, handle, catalog.course.id)
    return LearnerSnapshot(
        handle=handle,
        course_id=catalog.course.id,
        current_session=course_release.session_reached,
        taught_commands=tuple(
            sorted(catalog.commands_available_through(course_release.session_reached)),
        ),
        taught_skills=tuple(
            sorted(catalog.skills_available_through(course_release.session_reached))
        ),
        pending_quests=_pending_quest_ids(
            database_connection,
            catalog,
            handle,
            course_release.session_reached,
            completed_quest_ids,
        ),
        completed_quests=_ordered_known_quest_ids(catalog, completed_quest_ids),
        score=score,
        tier=current_tier_id(catalog, score),
        recent_help_topics=_recent_help_topics(database_connection, handle),
    )


def _pending_quest_ids(
    database_connection: sqlite3.Connection,
    catalog: CourseCatalog,
    handle: str,
    session_reached: str,
    completed_quest_ids: frozenset[str],
) -> tuple[str, ...]:
    available_quest_ids = frozenset(
        quest.id for quest in catalog.quests_available_through(session_reached)
    )
    assigned_incomplete_quests = tuple(
        catalog.quest(assignment.quest_id)
        for assignment in list_assignments(database_connection, handle, catalog.course.id)
        if assignment.quest_id in available_quest_ids
        and assignment.quest_id not in completed_quest_ids
    )
    next_quest = catalog.next_assignable_quest(session_reached, completed_quest_ids)
    pending_quests = assigned_incomplete_quests
    if next_quest is not None and next_quest.id not in {
        quest.id for quest in assigned_incomplete_quests
    }:
        pending_quests = (*pending_quests, next_quest)
    return tuple(quest.id for quest in catalog.prioritized_quests(session_reached, pending_quests))


def _ordered_known_quest_ids(
    catalog: CourseCatalog,
    quest_ids: frozenset[str],
) -> tuple[str, ...]:
    return tuple(quest.id for quest in catalog.course.quests if quest.id in quest_ids)


def _recent_help_topics(database_connection: sqlite3.Connection, handle: str) -> tuple[str, ...]:
    seen_topics: set[str] = set()
    topics: list[str] = []
    for interaction in list_recent_help_interactions(database_connection, handle, limit=10):
        for topic_tag in interaction.topic_tags:
            if topic_tag not in seen_topics:
                seen_topics.add(topic_tag)
                topics.append(topic_tag)
    return tuple(topics)
