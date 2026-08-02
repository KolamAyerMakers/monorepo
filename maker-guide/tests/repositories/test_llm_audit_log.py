"""Tests for restricted LLM audit log repository functions."""

from __future__ import annotations

from pathlib import Path

from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.llm_audit_log import (
    LlmAuditLog,
    append_llm_audit_log,
    count_llm_audit_logs,
    delete_llm_audit_logs_expired_before,
    list_llm_audit_logs,
)
from tests.repositories.helpers import COURSE_ID, TIMESTAMP, write_learner


def test_llm_audit_log_round_trips_full_request_and_response(
    migrated_database_path: Path,
) -> None:
    """Restricted audit rows store full LLM request and response payloads."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        audit_log_id = append_llm_audit_log(database_connection, _llm_audit_log())

        assert list_llm_audit_logs(database_connection, "alice", limit=10) == [
            LlmAuditLog(
                id=audit_log_id,
                handle="alice",
                course_id=COURSE_ID,
                source="irc",
                created_at=TIMESTAMP,
                provider="openrouter",
                model="deepseek/deepseek-v4-flash",
                status="answered",
                request={"messages": [{"role": "user", "content": "private question"}]},
                response={"raw_text": "raw private answer", "displayed_text": "safe answer"},
                expires_at="2026-10-09T09:00:00Z",
            ),
        ]


def test_delete_llm_audit_logs_expired_before_keeps_unexpired_rows(
    migrated_database_path: Path,
) -> None:
    """Expired restricted LLM audit rows can be pruned without touching current rows."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        append_llm_audit_log(
            database_connection,
            _llm_audit_log(expires_at="2026-09-01T00:00:00Z"),
        )
        append_llm_audit_log(
            database_connection,
            _llm_audit_log(expires_at="2026-11-01T00:00:00Z"),
        )

        deleted_count = delete_llm_audit_logs_expired_before(
            database_connection,
            "2026-10-01T00:00:00Z",
        )

        assert deleted_count == 1
        assert count_llm_audit_logs(database_connection) == 1


def _llm_audit_log(expires_at: str = "2026-10-09T09:00:00Z") -> LlmAuditLog:
    return LlmAuditLog(
        id=None,
        handle="alice",
        course_id=COURSE_ID,
        source="irc",
        created_at=TIMESTAMP,
        provider="openrouter",
        model="deepseek/deepseek-v4-flash",
        status="answered",
        request={"messages": [{"role": "user", "content": "private question"}]},
        response={"raw_text": "raw private answer", "displayed_text": "safe answer"},
        expires_at=expires_at,
    )
