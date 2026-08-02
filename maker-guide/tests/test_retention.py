"""Tests for raw observation retention cleanup."""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pytest

from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.progress.models import QuestAttemptInput
from maker_guide.progress.service import current_quest, record_attempt
from maker_guide.repositories.cohort_membership import CohortMembership, upsert_membership
from maker_guide.repositories.command_observation import (
    CommandObservation,
    add_command_observation,
    list_recent_command_observations,
)
from maker_guide.repositories.course_release import CourseRelease, upsert_course_release
from maker_guide.repositories.helpers import connect_database, transaction
from maker_guide.repositories.learner import Learner, upsert_learner
from maker_guide.repositories.llm_audit_log import (
    LlmAuditLog,
    append_llm_audit_log,
    count_llm_audit_logs,
)
from maker_guide.repositories.quest_attempt import get_quest_attempt
from maker_guide.repositories.session_objective_completion import (
    SessionObjectiveCompletion,
    complete_session_objective,
)
from maker_guide.retention import (
    llm_audit_expires_at,
    prune_command_observations,
    prune_llm_audit_logs,
)


def test_prune_command_observations_waits_until_retention_expires(
    migrated_database_path: Path,
) -> None:
    """Raw observations are retained through 30 days after course end."""
    cutoff_date = CATALOG.course.ends_on + timedelta(days=30)
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        add_command_observation(database_connection, _command_observation("whoami"))

        retention_result = prune_command_observations(
            database_connection,
            CATALOG,
            today=cutoff_date,
        )

        assert retention_result.cleanup_due is False
        assert retention_result.deleted_count == 0
        assert _observed_commands(database_connection) == ["whoami"]


def test_prune_command_observations_keeps_attempt_evidence_summaries(
    migrated_database_path: Path,
) -> None:
    """Quest attempt evidence survives after raw command observations are pruned."""
    cutoff_date = CATALOG.course.ends_on + timedelta(days=30)
    cutoff_at = f"{cutoff_date.isoformat()}T00:00:00Z"
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        current_quest(
            database_connection,
            CATALOG,
            handle="alice",
            assigned_at="2026-07-19T09:00:00Z",
            source="chat",
        )
        add_command_observation(
            database_connection,
            _command_observation("whoami", observed_at="2026-07-19T09:00:00Z"),
        )
        add_command_observation(
            database_connection,
            _command_observation("date", observed_at=cutoff_at),
        )
        attempt_result = record_attempt(
            database_connection,
            CATALOG,
            QuestAttemptInput(
                handle="alice",
                quest_id="prove-shell-alive",
                attempted_at="2026-07-19T09:01:00Z",
                source="chat",
                outcome="failed",
                failure_reason="missing-command",
                evidence={"matched_count": 1, "validation_type": "command_history"},
            ),
        )

        retention_result = prune_command_observations(
            database_connection,
            CATALOG,
            today=cutoff_date + timedelta(days=1),
        )

        assert retention_result.cleanup_due is True
        assert retention_result.deleted_count == 1
        assert _observed_commands(database_connection) == ["date"]
        if attempt_result.attempt.id is None:
            raise AssertionError("expected attempt id")
        stored_attempt = get_quest_attempt(database_connection, attempt_result.attempt.id)
        assert stored_attempt is not None
        assert stored_attempt.evidence == {
            "matched_count": 1,
            "validation_type": "command_history",
        }


def test_prune_command_observations_is_nested_transaction_safe(
    migrated_database_path: Path,
) -> None:
    """Observation pruning rolls back with an outer transaction."""
    cutoff_date = CATALOG.course.ends_on + timedelta(days=31)
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        add_command_observation(database_connection, _command_observation("whoami"))
        with pytest.raises(RuntimeError, match="rollback outer transaction"):
            _prune_observations_then_raise(database_connection, cutoff_date)

        assert _observed_commands(database_connection) == ["whoami"]


def test_llm_audit_expires_after_ninety_days() -> None:
    """Full LLM audit rows have an explicit 90-day retention timestamp."""
    assert llm_audit_expires_at("2026-07-19T09:00:00Z") == "2026-10-17T09:00:00Z"


def test_prune_llm_audit_logs_deletes_expired_rows(migrated_database_path: Path) -> None:
    """Restricted LLM audit retention prunes expired full request/response logs."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        append_llm_audit_log(
            database_connection,
            _llm_audit_log(expires_at="2026-10-01T00:00:00Z"),
        )
        append_llm_audit_log(
            database_connection,
            _llm_audit_log(expires_at="2026-11-01T00:00:00Z"),
        )

        retention_result = prune_llm_audit_logs(
            database_connection,
            now="2026-10-15T00:00:00Z",
        )

        assert retention_result.cutoff_at == "2026-10-15T00:00:00Z"
        assert retention_result.deleted_count == 1
        assert count_llm_audit_logs(database_connection) == 1


def test_prune_llm_audit_logs_is_nested_transaction_safe(migrated_database_path: Path) -> None:
    """LLM audit pruning rolls back with an outer transaction."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        append_llm_audit_log(
            database_connection,
            _llm_audit_log(expires_at="2026-10-01T00:00:00Z"),
        )
        with pytest.raises(RuntimeError, match="rollback outer transaction"):
            _prune_llm_audit_then_raise(database_connection)

        assert count_llm_audit_logs(database_connection) == 1


def _prune_observations_then_raise(
    database_connection: sqlite3.Connection,
    cutoff_date: date,
) -> None:
    with transaction(database_connection):
        prune_command_observations(database_connection, CATALOG, today=cutoff_date)
        raise RuntimeError("rollback outer transaction")


def _prune_llm_audit_then_raise(database_connection: sqlite3.Connection) -> None:
    with transaction(database_connection):
        prune_llm_audit_logs(database_connection, now="2026-10-15T00:00:00Z")
        raise RuntimeError("rollback outer transaction")


def _write_member(database_connection: sqlite3.Connection) -> None:
    upsert_learner(
        database_connection,
        Learner(
            handle="alice",
            joined_at="2026-07-18T09:00:00Z",
            tagline=None,
            created_at="2026-07-18T09:00:00Z",
        ),
    )
    upsert_membership(
        database_connection,
        CohortMembership(
            handle="alice",
            course_id=CATALOG.course.id,
            joined_at="2026-07-18T09:00:00Z",
        ),
    )
    upsert_course_release(
        database_connection,
        CourseRelease(
            course_id=CATALOG.course.id,
            session_reached="S1",
            released_at="2026-07-18T09:00:00Z",
        ),
    )
    for objective in CATALOG.session("S1").objectives:
        complete_session_objective(
            database_connection,
            SessionObjectiveCompletion(
                handle="alice",
                course_id=CATALOG.course.id,
                session_id="S1",
                objective_id=objective.id,
                completed_at="2026-07-18T09:00:00Z",
                evidence_json="{}",
            ),
        )


def _command_observation(
    command: str,
    observed_at: str = "2026-07-19T09:00:00Z",
) -> CommandObservation:
    return CommandObservation(
        id=None,
        handle="alice",
        course_id=CATALOG.course.id,
        command=command,
        cwd="/home/alice",
        phase="after",
        exit_status=0,
        observed_at=observed_at,
    )


def _llm_audit_log(expires_at: str) -> LlmAuditLog:
    return LlmAuditLog(
        id=None,
        handle="alice",
        course_id=CATALOG.course.id,
        source="test",
        created_at="2026-07-19T09:00:00Z",
        provider="openrouter",
        model="deepseek/deepseek-v4-flash",
        status="answered",
        request={"messages": [{"role": "user", "content": "private"}]},
        response={"raw_text": "raw", "displayed_text": "safe"},
        expires_at=expires_at,
    )


def _observed_commands(database_connection: sqlite3.Connection) -> list[str]:
    return [
        observation.command
        for observation in list_recent_command_observations(
            database_connection,
            "alice",
            CATALOG.course.id,
            observed_since="0000-01-01T00:00:00Z",
            limit=10,
        )
    ]
