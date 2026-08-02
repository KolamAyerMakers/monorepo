"""Tests for operational status and recovery checks."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer._click.exceptions import BadParameter

from maker_guide.cli.ops import run
from maker_guide.config import DEFAULT_CONFIG_PATH
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.projections.makers import MakersProjectionOptions, sync_makers_projection
from maker_guide.repositories.audit_event import AuditEvent, append_audit_event
from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.outbox_item import (
    GROUP_SYNC_OUTBOX_KIND,
    PROJECTION_OUTBOX_KIND,
    OutboxItem,
    OutboxStatus,
    enqueue_outbox_item,
)
from maker_guide.repositories.quest_attempt import QuestAttempt, record_quest_attempt
from tests.repositories.helpers import COURSE_ID, TIMESTAMP, write_learner


def test_ops_status_reports_recovery_backlogs(
    migrated_database_path: Path,
    temporary_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Status prints audit, outbox, migration, integrity, and projection state."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        append_audit_event(database_connection, _audit_event())
        enqueue_outbox_item(database_connection, _outbox_item(PROJECTION_OUTBOX_KIND, "pending"))
        enqueue_outbox_item(database_connection, _outbox_item(GROUP_SYNC_OUTBOX_KIND, "failed"))
        sync_makers_projection(
            database_connection,
            CATALOG,
            MakersProjectionOptions(
                makers_root=temporary_path / "makers",
                projected_at=TIMESTAMP,
                process_outbox=False,
            ),
        )

    assert run(["status", "--database", str(migrated_database_path)]) == 0

    output = capsys.readouterr().out
    assert f"database_path={migrated_database_path}" in output
    assert "sqlite_integrity=ok" in output
    assert "migration_revision=" in output
    assert "migration_head=20260801_0016" in output
    assert "audit_unexported=1" in output
    assert "unsupported_validation_attempts=0" in output
    assert "outbox kind=group_sync status=failed count=1" in output
    assert "outbox kind=projection status=pending count=1" in output
    assert "makers_projection=version:13" in output
    assert (
        f"migration_state_command=maker-guide-db --config {DEFAULT_CONFIG_PATH} current" in output
    )


def test_ops_check_passes_after_projection_sync(
    migrated_database_path: Path,
    temporary_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Check exits cleanly when repairable projections and queues are current."""
    with connect_database(migrated_database_path) as database_connection:
        sync_makers_projection(
            database_connection,
            CATALOG,
            MakersProjectionOptions(
                makers_root=temporary_path / "makers",
                projected_at=TIMESTAMP,
            ),
        )

    assert run(["check", "--database", str(migrated_database_path)]) == 0
    assert "Operational checks passed." in capsys.readouterr().out


def test_ops_check_fails_on_repair_backlogs(
    migrated_database_path: Path,
    temporary_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Check exits nonzero when audit export or side-effect workers are behind."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        sync_makers_projection(
            database_connection,
            CATALOG,
            MakersProjectionOptions(
                makers_root=temporary_path / "makers",
                projected_at=TIMESTAMP,
            ),
        )
        append_audit_event(database_connection, _audit_event())
        enqueue_outbox_item(database_connection, _outbox_item(GROUP_SYNC_OUTBOX_KIND, "failed"))

    assert run(["check", "--database", str(migrated_database_path)]) == 1

    error_output = capsys.readouterr().err
    assert "audit export backlog is 1; maximum is 0" in error_output
    assert "outbox backlog group_sync/failed has 1 rows" in error_output


def test_ops_check_fails_when_makers_projection_is_missing(
    migrated_database_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Projection drift is visible before `/makers` has been regenerated."""
    assert run(["check", "--database", str(migrated_database_path)]) == 1
    assert "makers projection is missing" in capsys.readouterr().err


def test_ops_check_fails_on_unsupported_validation_attempts(
    migrated_database_path: Path,
    temporary_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Impossible unsupported validation attempts are surfaced in ops checks."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        sync_makers_projection(
            database_connection,
            CATALOG,
            MakersProjectionOptions(
                makers_root=temporary_path / "makers",
                projected_at=TIMESTAMP,
            ),
        )
        record_quest_attempt(database_connection, _unsupported_validation_attempt())

    assert run(["status", "--database", str(migrated_database_path)]) == 0
    assert "unsupported_validation_attempts=1" in capsys.readouterr().out

    assert run(["check", "--database", str(migrated_database_path)]) == 1
    assert "unsupported validation attempts: 1" in capsys.readouterr().err


def test_ops_check_fails_when_migration_revision_is_stale(
    migrated_database_path: Path,
    temporary_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Stale migrations fail even when the revision table is present."""
    with connect_database(migrated_database_path) as database_connection:
        sync_makers_projection(
            database_connection,
            CATALOG,
            MakersProjectionOptions(
                makers_root=temporary_path / "makers",
                projected_at=TIMESTAMP,
            ),
        )
        database_connection.execute(
            "update alembic_version set version_num = ?",
            ("20260529_0001",),
        )

    assert run(["check", "--database", str(migrated_database_path)]) == 1
    assert "migration revision is 20260529_0001; expected 20260801_0016" in capsys.readouterr().err


def test_ops_check_rejects_negative_audit_backlog_limit(migrated_database_path: Path) -> None:
    """Ops thresholds cannot be negative."""
    with pytest.raises(BadParameter, match=r"x>=0"):
        run(
            [
                "check",
                "--database",
                str(migrated_database_path),
                "--max-unexported-audit-events",
                "-1",
            ],
        )


def _audit_event() -> AuditEvent:
    return AuditEvent(
        id=None,
        event_type="ops_test",
        handle="alice",
        source="test",
        created_at=TIMESTAMP,
        payload={"course_id": COURSE_ID},
        exported_at=None,
    )


def _outbox_item(kind: str, status: OutboxStatus) -> OutboxItem:
    match kind:
        case matched_kind if matched_kind == PROJECTION_OUTBOX_KIND:
            return OutboxItem(
                id=None,
                kind=kind,
                status=status,
                created_at=TIMESTAMP,
                processed_at=None,
                payload={"handle": "alice", "course_id": COURSE_ID, "reason": "enrollment"},
            )
        case matched_kind if matched_kind == GROUP_SYNC_OUTBOX_KIND:
            return OutboxItem(
                id=None,
                kind=kind,
                status=status,
                created_at=TIMESTAMP,
                processed_at=None,
                payload={
                    "handle": "alice",
                    "course_id": COURSE_ID,
                    "group_names": [COURSE_ID],
                    "reason": "group_grant_intended",
                },
            )
        case _:
            return OutboxItem(
                id=None,
                kind=kind,
                status=status,
                created_at=TIMESTAMP,
                processed_at=None,
                payload={"course_id": COURSE_ID},
            )


def _unsupported_validation_attempt() -> QuestAttempt:
    return QuestAttempt(
        id=None,
        handle="alice",
        course_id=COURSE_ID,
        quest_id="prove-shell-alive",
        attempted_at=TIMESTAMP,
        source="test",
        outcome="failed",
        failure_reason="unsupported-validation",
        evidence={"validation_type": "unsupported"},
    )
