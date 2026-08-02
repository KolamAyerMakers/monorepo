"""Repository queries for the `/makers` projection."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import cast


@dataclass(frozen=True, kw_only=True, slots=True)
class MakerLearnerState:
    """Aggregated learner state for one course projection."""

    handle: str
    """Shared learner id."""
    course_id: str
    """Course id from the Python curriculum catalog."""
    joined_at: str
    """ISO timestamp for when the learner joined this cohort."""
    rank_eligible: bool
    """Whether the learner belongs in the public course ranking."""
    session_reached: str | None
    """Latest reached session id, if known."""
    score_total: int
    """Derived course score total."""
    completed_quest_count: int
    """Number of completed quests in this course."""
    last_score_at: str | None
    """ISO timestamp for the latest score ledger entry, if any."""


@dataclass(frozen=True, kw_only=True, slots=True)
class MakerCompletedQuest:
    """Completed quest row used by `/makers/solves`."""

    handle: str
    """Shared learner id."""
    quest_id: str
    """Quest id from the Python curriculum catalog."""
    completed_at: str
    """ISO timestamp for when the quest was completed."""


@dataclass(frozen=True, kw_only=True, slots=True)
class MakerCompletedSessionObjective:
    """Completed session objective used by the learner progress card."""

    handle: str
    """Shared learner id."""
    session_id: str
    """Session id from the Python curriculum catalog."""
    objective_id: str
    """Objective id from the Python curriculum catalog."""
    completed_at: str
    """ISO timestamp for when the objective was completed."""


def list_maker_learner_states(
    database_connection: sqlite3.Connection,
    course_id: str,
) -> list[MakerLearnerState]:
    """Return course learner state needed for `/makers` files."""
    state_records = cast(
        "list[tuple[str, str, str, int, str | None, int, int, str | None]]",
        database_connection.execute(
            """
            with score_totals as (
                select
                    handle,
                    course_id,
                    sum(amount) as score_total,
                    max(created_at) as last_score_at
                from score_ledger
                where course_id = ?
                group by handle, course_id
            ),
            completion_totals as (
                select handle, course_id, count(*) as completed_quest_count
                from quest_completions
                where course_id = ?
                group by handle, course_id
            )
            select
                cohort_memberships.handle,
                cohort_memberships.course_id,
                cohort_memberships.joined_at,
                cohort_memberships.rank_eligible,
                course_releases.session_reached,
                coalesce(score_totals.score_total, 0),
                coalesce(completion_totals.completed_quest_count, 0),
                score_totals.last_score_at
            from cohort_memberships
            left join course_releases
                on course_releases.course_id = cohort_memberships.course_id
            left join score_totals
                on score_totals.handle = cohort_memberships.handle
                and score_totals.course_id = cohort_memberships.course_id
            left join completion_totals
                on completion_totals.handle = cohort_memberships.handle
                and completion_totals.course_id = cohort_memberships.course_id
            where cohort_memberships.course_id = ?
            order by cohort_memberships.handle
            """,
            (course_id, course_id, course_id),
        ).fetchall(),
    )
    return [
        MakerLearnerState(
            handle=state_record[0],
            course_id=state_record[1],
            joined_at=state_record[2],
            rank_eligible=bool(state_record[3]),
            session_reached=state_record[4],
            score_total=state_record[5],
            completed_quest_count=state_record[6],
            last_score_at=state_record[7],
        )
        for state_record in state_records
    ]


def list_maker_completed_quests(
    database_connection: sqlite3.Connection,
    course_id: str,
) -> list[MakerCompletedQuest]:
    """Return completed quests for all learners in a course."""
    completion_records = cast(
        "list[tuple[str, str, str]]",
        database_connection.execute(
            """
            select handle, quest_id, completed_at
            from quest_completions
            where course_id = ?
            order by handle, completed_at, quest_id
            """,
            (course_id,),
        ).fetchall(),
    )
    return [
        MakerCompletedQuest(
            handle=completion_record[0],
            quest_id=completion_record[1],
            completed_at=completion_record[2],
        )
        for completion_record in completion_records
    ]


def list_maker_completed_session_objectives(
    database_connection: sqlite3.Connection,
    course_id: str,
) -> list[MakerCompletedSessionObjective]:
    """Return completed session objectives for all learners in a course."""
    completion_records = cast(
        "list[tuple[str, str, str, str]]",
        database_connection.execute(
            """
            select handle, session_id, objective_id, completed_at
            from session_objective_completions
            where course_id = ?
            order by handle, completed_at, session_id, objective_id
            """,
            (course_id,),
        ).fetchall(),
    )
    return [
        MakerCompletedSessionObjective(
            handle=completion_record[0],
            session_id=completion_record[1],
            objective_id=completion_record[2],
            completed_at=completion_record[3],
        )
        for completion_record in completion_records
    ]
