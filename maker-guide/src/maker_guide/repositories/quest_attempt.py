"""Quest attempt repository functions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import cast

from maker_guide.repositories.helpers import JsonPayload, dump_json, last_inserted_id, load_json


@dataclass(frozen=True, kw_only=True, slots=True)
class QuestAttempt:
    """One quest validation attempt."""

    id: int | None
    """SQLite-generated attempt id, absent before insert."""
    handle: str
    """Shared learner id."""
    course_id: str
    """Course id from the Python curriculum catalog."""
    quest_id: str
    """Quest id from the Python curriculum catalog."""
    attempted_at: str
    """ISO timestamp for when validation ran."""
    source: str
    """Source that requested validation."""
    outcome: str
    """Validation outcome, such as passed or failed."""
    failure_reason: str | None
    """Optional deterministic reason for validation failure."""
    evidence: JsonPayload
    """Validation facts used to decide the outcome."""


def record_quest_attempt(database_connection: sqlite3.Connection, attempt: QuestAttempt) -> int:
    """Append a quest validation attempt."""
    return last_inserted_id(
        database_connection.execute(
            """
            insert into quest_attempts
                (handle, course_id, quest_id, attempted_at, source, outcome,
                failure_reason, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attempt.handle,
                attempt.course_id,
                attempt.quest_id,
                attempt.attempted_at,
                attempt.source,
                attempt.outcome,
                attempt.failure_reason,
                dump_json(attempt.evidence),
            ),
        ),
    )


def get_quest_attempt(
    database_connection: sqlite3.Connection,
    attempt_id: int,
) -> QuestAttempt | None:
    """Return a quest validation attempt."""
    attempt_record = cast(
        "tuple[int, str, str, str, str, str, str, str | None, str] | None",
        database_connection.execute(
            """
            select id, handle, course_id, quest_id, attempted_at, source, outcome,
                failure_reason, evidence_json
            from quest_attempts
            where id = ?
            """,
            (attempt_id,),
        ).fetchone(),
    )
    if attempt_record is None:
        return None
    return QuestAttempt(
        id=attempt_record[0],
        handle=attempt_record[1],
        course_id=attempt_record[2],
        quest_id=attempt_record[3],
        attempted_at=attempt_record[4],
        source=attempt_record[5],
        outcome=attempt_record[6],
        failure_reason=attempt_record[7],
        evidence=load_json(attempt_record[8]),
    )


def count_quest_attempts_by_failure_reason(
    database_connection: sqlite3.Connection,
    failure_reason: str,
) -> int:
    """Return the number of quest attempts with one failure reason."""
    return cast(
        "tuple[int]",
        database_connection.execute(
            "select count(*) from quest_attempts where failure_reason = ?",
            (failure_reason,),
        ).fetchone(),
    )[0]
