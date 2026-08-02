"""Tests for audit JSONL export CLI."""

from __future__ import annotations

import fcntl
import json
import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import cast

import pytest
from typer._click.exceptions import BadParameter

from maker_guide.cli.export_audit import run
from maker_guide.repositories.audit_event import (
    AuditEvent,
    append_audit_event,
    list_unexported_audit_events,
)
from maker_guide.repositories.helpers import connect_database
from tests.repositories.helpers import COURSE_ID, write_learner


def test_export_audit_cli_writes_jsonl_and_marks_rows(
    migrated_database_path: Path,
    temporary_path: Path,
) -> None:
    """Unexported audit rows are appended to date JSONL and marked exported."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        audit_id = append_audit_event(database_connection, _audit_event("quest_completed"))

    assert (
        run(
            [
                "--database",
                str(migrated_database_path),
                "--audit-root",
                str(temporary_path / "audit"),
            ],
        )
        == 0
    )

    assert _jsonl_rows(temporary_path / "audit" / "2026-07-19.jsonl") == [
        {
            "audit_id": audit_id,
            "created_at": "2026-07-19T09:00:00Z",
            "event_type": "quest_completed",
            "handle": "alice",
            "payload": {"course_id": COURSE_ID},
            "source": "test",
        },
    ]
    with connect_database(migrated_database_path) as database_connection:
        assert list_unexported_audit_events(database_connection, 10) == []

    assert (
        run(
            [
                "--database",
                str(migrated_database_path),
                "--audit-root",
                str(temporary_path / "audit"),
            ],
        )
        == 0
    )
    assert len(_jsonl_rows(temporary_path / "audit" / "2026-07-19.jsonl")) == 1


def test_export_audit_cli_creates_restrictive_export_paths(
    migrated_database_path: Path,
    temporary_path: Path,
) -> None:
    """Audit export directories, locks, and JSONL files are not world-readable."""
    audit_root = temporary_path / "audit"
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        append_audit_event(database_connection, _audit_event("quest_completed"))

    previous_umask = os.umask(0)
    try:
        assert (
            run(["--database", str(migrated_database_path), "--audit-root", str(audit_root)]) == 0
        )
    finally:
        os.umask(previous_umask)

    assert audit_root.stat().st_mode & 0o777 == 0o700
    assert (audit_root / ".export.lock").stat().st_mode & 0o777 == 0o600
    assert (audit_root / "2026-07-19.jsonl").stat().st_mode & 0o777 == 0o600


def test_export_audit_allows_duplicate_lines_after_append_before_mark_crash(
    migrated_database_path: Path,
    temporary_path: Path,
) -> None:
    """Rerun after append-before-mark crash may duplicate safely by audit_id."""
    audit_root = temporary_path / "audit"
    audit_root.mkdir()
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        audit_id = append_audit_event(database_connection, _audit_event("score_awarded"))

    (audit_root / "2026-07-19.jsonl").write_text(
        json.dumps(
            {
                "audit_id": audit_id,
                "created_at": "2026-07-19T09:00:00Z",
                "event_type": "score_awarded",
                "handle": "alice",
                "payload": {"course_id": COURSE_ID},
                "source": "test",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    assert (
        run(
            [
                "--database",
                str(migrated_database_path),
                "--audit-root",
                str(audit_root),
            ],
        )
        == 0
    )

    rows = _jsonl_rows(audit_root / "2026-07-19.jsonl")
    assert [row["audit_id"] for row in rows] == [audit_id, audit_id]
    with connect_database(migrated_database_path) as database_connection:
        assert list_unexported_audit_events(database_connection, 10) == []


def test_export_audit_cli_rejects_concurrent_exporter(
    migrated_database_path: Path,
    temporary_path: Path,
) -> None:
    """A held audit-root lock prevents concurrent JSONL export attempts."""
    audit_root = temporary_path / "audit"
    audit_root.mkdir()
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        audit_id = append_audit_event(database_connection, _audit_event("quest_completed"))

    with _held_export_lock(audit_root):
        assert (
            run(
                [
                    "--database",
                    str(migrated_database_path),
                    "--audit-root",
                    str(audit_root),
                ],
            )
            == 1
        )

    assert not (audit_root / "2026-07-19.jsonl").exists()
    with connect_database(migrated_database_path) as database_connection:
        assert [
            audit_event.id for audit_event in list_unexported_audit_events(database_connection, 10)
        ] == [audit_id]

    assert (
        run(
            [
                "--database",
                str(migrated_database_path),
                "--audit-root",
                str(audit_root),
            ],
        )
        == 0
    )
    assert [row["audit_id"] for row in _jsonl_rows(audit_root / "2026-07-19.jsonl")] == [
        audit_id,
    ]


@pytest.mark.parametrize("symlink_name", [".export.lock", "2026-07-19.jsonl"])
def test_export_audit_cli_rejects_symlinked_export_paths(
    migrated_database_path: Path,
    temporary_path: Path,
    symlink_name: str,
) -> None:
    """Audit export does not follow attacker-controlled lock or partition symlinks."""
    audit_root = temporary_path / "audit"
    symlink_target = temporary_path / "target"
    audit_root.mkdir()
    symlink_target.write_text("original\n", encoding="utf-8")
    (audit_root / symlink_name).symlink_to(symlink_target)
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        audit_id = append_audit_event(database_connection, _audit_event("quest_completed"))

    assert run(["--database", str(migrated_database_path), "--audit-root", str(audit_root)]) == 1

    assert symlink_target.read_text(encoding="utf-8") == "original\n"
    with connect_database(migrated_database_path) as database_connection:
        assert [
            audit_event.id for audit_event in list_unexported_audit_events(database_connection, 10)
        ] == [audit_id]


@pytest.mark.parametrize("limit", ["0", "-1"])
def test_export_audit_cli_rejects_non_positive_limit(
    migrated_database_path: Path,
    temporary_path: Path,
    limit: str,
) -> None:
    """Audit export limits must not turn into unbounded SQLite queries."""
    with pytest.raises(BadParameter, match=r"x>=1"):
        run(
            [
                "--database",
                str(migrated_database_path),
                "--audit-root",
                str(temporary_path / "audit"),
                "--limit",
                limit,
            ],
        )


def _audit_event(event_type: str) -> AuditEvent:
    return AuditEvent(
        id=None,
        event_type=event_type,
        handle="alice",
        source="test",
        created_at="2026-07-19T09:00:00Z",
        payload={"course_id": COURSE_ID},
        exported_at=None,
    )


def _jsonl_rows(path: Path) -> list[dict[str, object]]:
    return [
        cast("dict[str, object]", json.loads(line))
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


@contextmanager
def _held_export_lock(audit_root: Path) -> Generator[None]:
    with (audit_root / ".export.lock").open("a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
