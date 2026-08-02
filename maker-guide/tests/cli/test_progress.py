"""Tests for learner progress reporting CLI."""

from __future__ import annotations

import sqlite3
import subprocess
from datetime import date
from pathlib import Path

import pytest

from maker_guide.cli import progress
from maker_guide.cli.progress import run
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.repositories.cohort_membership import (
    CohortMembership,
    upsert_membership,
)
from maker_guide.repositories.course_release import (
    CourseRelease,
    get_course_release,
    upsert_course_release,
)
from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.learner import Learner, upsert_learner
from maker_guide.repositories.quest_completion import QuestCompletion, complete_quest
from maker_guide.repositories.score_ledger import ScoreLedgerEntry, add_score_entry
from maker_guide.repositories.session_objective_completion import (
    SessionObjectiveCompletion,
    complete_session_objective,
)


def test_progress_cli_separates_students_from_non_students(
    migrated_database_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Progress list separates ranked students from course participants."""
    with connect_database(migrated_database_path) as database_connection:
        _write_progress_state(database_connection)
        _write_member(
            database_connection,
            "mentor",
            "2026-07-18T09:10:00Z",
            rank_eligible=False,
        )

    assert run(["--database", str(migrated_database_path)]) == 0

    output = capsys.readouterr().out
    assert "Student Progress (lf2607, course release: S2)" in output
    assert "Non-student Progress (lf2607, course release: S2)" in output
    assert "bob" in output
    assert "475" in output
    assert "newcomer" in output
    assert "alice" in output
    assert "25" in output
    assert "newcomer" in output
    assert "Last score" in output
    assert "mentor" in output


def test_progress_cli_hides_quests_before_course_release(
    migrated_database_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Progress show does not imply unreleased quests are available."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, "alice", "2026-07-18T09:00:00Z", session_reached=None)

    assert run(["show", "alice", "--database", str(migrated_database_path)]) == 0

    output = capsys.readouterr().out
    assert "Course release" in output
    assert "prove-shell-alive" not in output


def test_progress_cli_shows_single_learner(
    migrated_database_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Progress show includes learner summary and current-session quests."""
    with connect_database(migrated_database_path) as database_connection:
        _write_progress_state(database_connection)

    assert run(["show", "bob", "--database", str(migrated_database_path)]) == 0

    output = capsys.readouterr().out
    assert "bob Progress (lf2607)" in output
    assert "Score" in output
    assert "475" in output
    assert "Quest Progress" in output
    assert "done" in output
    assert "todo" in output
    assert "prove-shell-alive" in output
    assert "build-playground" in output


def test_progress_cli_rejects_unknown_learner(
    migrated_database_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Progress show exits nonzero for an unknown learner."""
    with connect_database(migrated_database_path) as database_connection:
        _write_progress_state(database_connection)

    assert run(["show", "mallory", "--database", str(migrated_database_path)]) == 2
    assert "Unknown learner: mallory" in capsys.readouterr().err


@pytest.mark.parametrize("session_id", ["S01", "s1"])
def test_progress_cli_releases_cohort(
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    session_id: str,
) -> None:
    """Release updates the shared course state."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, "alice", "2026-07-18T09:00:00Z", session_reached=None)
        _write_member(database_connection, "bob", "2026-07-18T09:05:00Z", session_reached=None)

    commands: list[tuple[str, ...]] = []

    def start_service(
        command: tuple[str, ...], **_keyword_arguments: object
    ) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(progress.subprocess, "run", start_service)

    assert run(["release", session_id, "--database", str(migrated_database_path)]) == 0
    assert commands == [
        ("/usr/bin/sudo", "-n", "/usr/bin/systemctl", "start", "maker-guide-build-docs.service")
    ]

    with connect_database(migrated_database_path) as database_connection:
        assert _session_reached(database_connection, "alice") == "S1"
        assert _session_reached(database_connection, "bob") == "S1"
    assert "released S1" in capsys.readouterr().out


def test_progress_cli_release_is_idempotent(
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Releasing the current session leaves shared course state unchanged."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, "alice", "2026-07-18T09:00:00Z", session_reached="S1")
        _write_member(database_connection, "bob", "2026-07-18T09:05:00Z", session_reached="S1")

    def unexpected_start_service(
        _command: tuple[str, ...], **_keyword_arguments: object
    ) -> subprocess.CompletedProcess[str]:
        raise AssertionError

    monkeypatch.setattr(progress.subprocess, "run", unexpected_start_service)

    assert run(["release", "S1", "--database", str(migrated_database_path)]) == 0

    with connect_database(migrated_database_path) as database_connection:
        assert _session_reached(database_connection, "alice") == "S1"
        assert _session_reached(database_connection, "bob") == "S1"


def test_progress_cli_live_shows_durable_session_progress(
    migrated_database_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Session progress shows every objective and quest from durable completions."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, "alice", "2026-07-18T09:00:00Z", session_reached="S1")
        _write_member(database_connection, "bob", "2026-07-18T09:05:00Z", session_reached="S1")
        complete_session_objective(
            database_connection,
            SessionObjectiveCompletion(
                handle="alice",
                course_id=CATALOG.course.id,
                session_id="S1",
                objective_id="join-course-irc",
                completed_at="2026-07-18T09:10:00Z",
                evidence_json="{}",
            ),
        )
        complete_quest(
            database_connection,
            _completion("alice", "prove-shell-alive", "2026-07-18T09:11:00Z"),
        )

    assert run(["live", "S1", "--database", str(migrated_database_path)]) == 0

    output = capsys.readouterr().out
    assert "Session Progress S1" in output
    assert "(lf2607)" in output
    assert "join-course-irc" in output
    assert "prove-shell-alive" in output
    assert "alice" in output
    assert "yes" in output
    assert "bob" in output


def test_progress_cli_live_defaults_to_current_session(
    migrated_database_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Session progress defaults to the dated class session."""

    def fixed_today(course: object) -> date:
        del course
        return date(2026, 7, 18)

    monkeypatch.setattr(
        "maker_guide.cli.progress._course_today",
        fixed_today,
    )
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, "alice", "2026-07-18T09:00:00Z", session_reached="S1")
        _write_member(database_connection, "bob", "2026-07-18T09:05:00Z", session_reached="S2")

    assert run(["live", "--database", str(migrated_database_path)]) == 0

    output = capsys.readouterr().out
    assert "Session Progress S1" in output
    assert "join-course-irc" in output


def _write_progress_state(database_connection: sqlite3.Connection) -> None:
    _write_member(database_connection, "alice", "2026-07-18T09:00:00Z")
    _write_member(database_connection, "bob", "2026-07-18T09:05:00Z")
    add_score_entry(
        database_connection,
        _score_entry("alice", 25, "prove-shell-alive", "2026-07-19T09:00:00Z"),
    )
    add_score_entry(
        database_connection,
        _score_entry("bob", 475, "prove-shell-alive", "2026-07-19T09:00:00Z"),
    )
    complete_quest(
        database_connection,
        _completion("alice", "prove-shell-alive", "2026-07-19T09:00:00Z"),
    )
    complete_quest(
        database_connection,
        _completion("bob", "prove-shell-alive", "2026-07-19T09:00:00Z"),
    )


def _write_member(
    database_connection: sqlite3.Connection,
    handle: str,
    joined_at: str,
    session_reached: str | None = "S2",
    *,
    rank_eligible: bool = True,
) -> None:
    upsert_learner(
        database_connection,
        Learner(handle=handle, joined_at=joined_at, tagline=None, created_at=joined_at),
    )
    upsert_membership(
        database_connection,
        CohortMembership(
            handle=handle,
            course_id=CATALOG.course.id,
            joined_at=joined_at,
            rank_eligible=rank_eligible,
        ),
    )
    if session_reached is not None:
        upsert_course_release(
            database_connection,
            CourseRelease(
                course_id=CATALOG.course.id,
                session_reached=session_reached,
                released_at=joined_at,
            ),
        )


def _session_reached(database_connection: sqlite3.Connection, handle: str) -> str | None:
    assert handle in {"alice", "bob"}
    course_release = get_course_release(database_connection, CATALOG.course.id)
    assert course_release is not None
    return course_release.session_reached


def _score_entry(
    handle: str,
    amount: int,
    quest_id: str,
    created_at: str,
) -> ScoreLedgerEntry:
    return ScoreLedgerEntry(
        id=None,
        handle=handle,
        course_id=CATALOG.course.id,
        amount=amount,
        reason="quest_completed",
        related_type="quest",
        related_id=quest_id,
        created_at=created_at,
    )


def _completion(handle: str, quest_id: str, completed_at: str) -> QuestCompletion:
    return QuestCompletion(
        handle=handle,
        course_id=CATALOG.course.id,
        quest_id=quest_id,
        attempt_id=None,
        completed_at=completed_at,
        source="test",
    )
