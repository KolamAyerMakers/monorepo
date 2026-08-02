"""Tests for restricted LLM audit pruning CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

from maker_guide.cli.prune_llm_audit import run
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.llm_audit_log import (
    LlmAuditLog,
    append_llm_audit_log,
    count_llm_audit_logs,
)
from tests.repositories.helpers import write_learner


def test_prune_llm_audit_cli_deletes_expired_restricted_logs(
    migrated_database_path: Path,
) -> None:
    """The CLI prunes restricted LLM audit rows from the configured database path."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        append_llm_audit_log(database_connection, _llm_audit_log())

    assert (
        run(
            [
                "--database",
                str(migrated_database_path),
                "--now",
                "2026-10-02T00:00:00Z",
            ],
        )
        == 0
    )

    with connect_database(migrated_database_path) as database_connection:
        assert count_llm_audit_logs(database_connection) == 0


@pytest.mark.parametrize(
    "now",
    [
        "2026-10-02T00:00:00Z",
        "2026-10-02T00:00:00+00:00",
        "2026-10-02T05:30:00+05:30",
    ],
)
def test_prune_llm_audit_cli_normalizes_now_offsets(
    migrated_database_path: Path,
    now: str,
) -> None:
    """Equivalent timezone-aware --now inputs compare correctly with stored Z timestamps."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        append_llm_audit_log(database_connection, _llm_audit_log())

    assert run(["--database", str(migrated_database_path), "--now", now]) == 0

    with connect_database(migrated_database_path) as database_connection:
        assert count_llm_audit_logs(database_connection) == 0


def _llm_audit_log() -> LlmAuditLog:
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
        expires_at="2026-10-01T00:00:00Z",
    )
