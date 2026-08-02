"""Tests for `/makers` projection writing."""

from __future__ import annotations

import fcntl
import json
import shutil
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import cast

import pytest

from maker_guide.cli.check_doc_links import find_missing_doc_references
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.projections import makers as makers_projection
from maker_guide.projections.makers import (
    MAKERS_PROJECTION_NAME,
    MakersProjectionError,
    MakersProjectionOptions,
    sync_makers_projection,
)
from maker_guide.repositories.cohort_membership import CohortMembership, upsert_membership
from maker_guide.repositories.course_release import CourseRelease, upsert_course_release
from maker_guide.repositories.helpers import connect_database, dump_json, transaction
from maker_guide.repositories.learner import Learner, upsert_learner
from maker_guide.repositories.outbox_item import (
    PENDING_OUTBOX_STATUS,
    PROJECTION_OUTBOX_KIND,
    OutboxItem,
    enqueue_outbox_item,
    list_pending_outbox_items_by_kind,
    list_retryable_outbox_items_by_kind,
    projection_outbox_item,
)
from maker_guide.repositories.peer_thank import PeerThank, add_peer_thank
from maker_guide.repositories.projection_version import get_projection_version
from maker_guide.repositories.quest_completion import QuestCompletion, complete_quest
from maker_guide.repositories.score_ledger import ScoreLedgerEntry, add_score_entry
from maker_guide.repositories.session_objective_completion import (
    SessionObjectiveCompletion,
    complete_session_objective,
)

PROJECTED_AT = "2026-07-25T09:00:00Z"
QUEST_CONTENT_PATH = Path(
    "quests/prove-shell-alive.md",
)
S01_SELF_STUDY_PATH = Path("sessions/S01/self-study.md")


def test_makers_projection_rebuilds_files_and_marks_projection_outbox(  # noqa: PLR0915 - One projection transaction.
    migrated_database_path: Path,
    temporary_path: Path,
) -> None:
    """The `/makers` projection is fully regenerated from SQLite state."""
    makers_root = temporary_path / "makers"
    documents_root = temporary_path / "docs"
    _write_stale_files(makers_root)
    (documents_root / "stale").mkdir(parents=True)
    (documents_root / "stale" / "doc.md").write_text("stale\n", encoding="utf-8")
    with connect_database(migrated_database_path) as database_connection:
        _write_projection_state(database_connection)
        peer_thank_id = add_peer_thank(
            database_connection,
            PeerThank(
                id=None,
                giver_handle="alice",
                recipient_handle="bob",
                course_id=CATALOG.course.id,
                reason="Explained SSH permissions",
                thanked_on="2026-07-25",
                created_at="2026-07-25T08:57:00Z",
            ),
        )
        add_score_entry(
            database_connection,
            ScoreLedgerEntry(
                id=None,
                handle="bob",
                course_id=CATALOG.course.id,
                amount=10,
                reason="peer_thank_received",
                related_type="peer_thank",
                related_id=str(peer_thank_id),
                created_at="2026-07-25T08:57:00Z",
            ),
        )
        complete_session_objective(
            database_connection,
            SessionObjectiveCompletion(
                handle="bob",
                course_id=CATALOG.course.id,
                session_id="S1",
                objective_id="join-course-irc",
                completed_at="2026-07-20T09:00:00Z",
                evidence_json="{}",
            ),
        )
        add_score_entry(
            database_connection,
            ScoreLedgerEntry(
                id=None,
                handle="bob",
                course_id=CATALOG.course.id,
                amount=365,
                reason="session_objective_completed",
                related_type="session_objective",
                related_id="S1:join-course-irc",
                created_at="2026-07-20T09:00:00Z",
            ),
        )
        enqueue_outbox_item(
            database_connection,
            _outbox_item(kind=PROJECTION_OUTBOX_KIND, created_at="2026-07-25T08:58:00Z"),
        )
        database_connection.execute(
            "update outbox_items set status = 'failed' where kind = ?",
            (PROJECTION_OUTBOX_KIND,),
        )
        enqueue_outbox_item(
            database_connection,
            _outbox_item(kind="irc", created_at="2026-07-25T08:59:00Z"),
        )

        result = sync_makers_projection(
            database_connection,
            CATALOG,
            MakersProjectionOptions(makers_root=makers_root, projected_at=PROJECTED_AT),
        )

        assert result.learner_count == 2
        assert result.processed_outbox_count == 1
        assert (makers_root / "bob" / "rank").read_text(encoding="utf-8") == "1\n"
        assert (makers_root / "bob" / "score").read_text(encoding="utf-8") == "475\n"
        assert (makers_root / "bob" / "tier").read_text(encoding="utf-8") == "newcomer\n"
        assert (makers_root / "alice" / "tier").read_text(encoding="utf-8") == "newcomer\n"
        assert (makers_root / "alice" / "tracks" / "lockouts").read_text(
            encoding="utf-8",
        ) == "none\n"
        assert json.loads((makers_root / "bob" / "thanks.json").read_text(encoding="utf-8")) == [
            {
                "created_at": "2026-07-25T08:57:00Z",
                "from": "alice",
                "reason": "Explained SSH permissions",
                "thanked_on": "2026-07-25",
            },
        ]
        assert json.loads(
            (makers_root / "bob" / "score-ledger.json").read_text(encoding="utf-8"),
        ) == [
            {
                "amount": 100,
                "created_at": "2026-07-19T09:00:00Z",
                "reason": "quest_completed",
                "related_id": "prove-shell-alive",
                "related_name": "Prove the shell is alive",
                "related_type": "quest",
                "peer_thank_giver": None,
                "peer_thank_reason": None,
            },
            {
                "amount": 365,
                "created_at": "2026-07-20T09:00:00Z",
                "reason": "session_objective_completed",
                "related_id": "S1:join-course-irc",
                "related_name": "Join the course IRC channel",
                "related_type": "session_objective",
                "peer_thank_giver": None,
                "peer_thank_reason": None,
            },
            {
                "amount": 10,
                "created_at": "2026-07-25T08:57:00Z",
                "reason": "peer_thank_received",
                "related_id": str(peer_thank_id),
                "related_name": None,
                "related_type": "peer_thank",
                "peer_thank_giver": "alice",
                "peer_thank_reason": "Explained SSH permissions",
            },
        ]
        quest_progress = cast(
            "dict[str, list[dict[str, str]]]",
            json.loads((makers_root / "bob" / "quests.json").read_text(encoding="utf-8")),
        )
        assert quest_progress["completed"] == [
            {
                "documentation_path": "quests/prove-shell-alive.md",
                "id": "prove-shell-alive",
                "title": "Prove the shell is alive",
            },
        ]
        assert [quest["id"] for quest in quest_progress["remaining"]] == [
            quest.id
            for quest in CATALOG.quests_available_through("S2")
            if quest.id != "prove-shell-alive"
        ]
        assert quest_progress["total"] == len(CATALOG.course.quests)
        objective_progress = cast(
            "dict[str, int | list[dict[str, str]]]",
            json.loads((makers_root / "bob" / "objectives.json").read_text(encoding="utf-8")),
        )
        assert objective_progress["completed"] == [
            {
                "documentation_path": "sessions/S01/self-study.md",
                "id": "join-course-irc",
                "title": "Join the course IRC channel",
            },
        ]
        assert objective_progress["total"] == sum(
            len(session.objectives) for session in CATALOG.course.sessions
        )
        session_progress = cast(
            "dict[str, list[dict[str, str]]]",
            json.loads((makers_root / "bob" / "sessions.json").read_text(encoding="utf-8")),
        )
        assert [session["id"] for session in session_progress["reached"]] == ["S1", "S2"]
        assert [session["id"] for session in session_progress["remaining"]] == [
            session.id for session in CATALOG.course.sessions[2:]
        ]
        assert (
            (documents_root / QUEST_CONTENT_PATH)
            .read_text(
                encoding="utf-8",
            )
            .startswith("# Prove the shell is alive\n")
        )
        assert "[whoami](../commands/whoami.md)" in (documents_root / QUEST_CONTENT_PATH).read_text(
            encoding="utf-8"
        )
        assert "[Time Zones](../../concepts/time-zones.md)" in (
            documents_root / S01_SELF_STUDY_PATH
        ).read_text(encoding="utf-8")
        command_index = (documents_root / "commands" / "README.md").read_text(encoding="utf-8")
        concept_index = (documents_root / "concepts" / "README.md").read_text(encoding="utf-8")
        quest_index = (documents_root / "quests" / "README.md").read_text(encoding="utf-8")
        assert "(whoami.md)" in command_index
        assert "(grep.md)" in command_index
        assert "(shell-basics.md)" in concept_index
        assert "(pipes.md)" in concept_index
        assert "### Go Deeper After S03" in concept_index
        assert "(prove-shell-alive.md)" in quest_index
        assert "(count-stream.md)" not in quest_index
        assert not (documents_root / "sessions" / "S03").exists()
        assert not (documents_root / "quests" / "count-stream.md").exists()
        assert not (makers_root / "content").exists()
        assert not (documents_root / "stale").exists()
        assert not (makers_root / "ghost").exists()
        assert not (makers_root / "alice" / "stale").exists()
        assert get_projection_version(database_connection, MAKERS_PROJECTION_NAME) is not None
        assert [
            outbox_item.kind
            for outbox_item in list_pending_outbox_items_by_kind(database_connection, "irc", 10)
        ] == ["irc"]
        assert (
            list_retryable_outbox_items_by_kind(
                database_connection,
                PROJECTION_OUTBOX_KIND,
                10,
            )
            == []
        )


def test_makers_projection_rebuilds_deleted_root_from_sqlite(
    migrated_database_path: Path,
    temporary_path: Path,
) -> None:
    """Deleting `/makers` is repairable because SQLite is authoritative."""
    makers_root = temporary_path / "makers"
    documents_root = temporary_path / "docs"
    with connect_database(migrated_database_path) as database_connection:
        _write_projection_state(database_connection)
        sync_makers_projection(
            database_connection,
            CATALOG,
            MakersProjectionOptions(makers_root=makers_root, projected_at=PROJECTED_AT),
        )

        shutil.rmtree(makers_root)

        result = sync_makers_projection(
            database_connection,
            CATALOG,
            MakersProjectionOptions(makers_root=makers_root, projected_at=PROJECTED_AT),
        )

        assert result.learner_count == 2
        assert (makers_root / "bob" / "score").read_text(encoding="utf-8") == "100\n"
        assert (makers_root / "alice" / "rank").read_text(encoding="utf-8") == "2\n"
    assert (documents_root / QUEST_CONTENT_PATH).exists()


def test_makers_projection_derives_key_auth_progress_from_s2_objective(
    migrated_database_path: Path,
    temporary_path: Path,
) -> None:
    """Key-auth status is a rebuildable S2 objective projection."""
    makers_root = temporary_path / "makers"
    objective_completion_time = "2026-07-25T09:15:00Z"
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, "alice", "2026-07-18T09:00:00Z")
        complete_quest(
            database_connection,
            _completion("alice", "prove-shell-alive", "2026-07-19T09:00:00Z"),
        )
        sync_makers_projection(
            database_connection,
            CATALOG,
            MakersProjectionOptions(makers_root=makers_root, projected_at=PROJECTED_AT),
        )
        assert (makers_root / "alice" / "key-auth-progress").read_text(encoding="utf-8") == (
            "pending\n"
        )

        complete_session_objective(
            database_connection,
            SessionObjectiveCompletion(
                handle="alice",
                course_id=CATALOG.course.id,
                session_id="S2",
                objective_id="ssh-public-key",
                completed_at=objective_completion_time,
                evidence_json="{}",
            ),
        )
        sync_makers_projection(
            database_connection,
            CATALOG,
            MakersProjectionOptions(makers_root=makers_root, projected_at=PROJECTED_AT),
        )
        expected_progress = f"reinforcement\ncompleted_at={objective_completion_time}\n"
        assert (makers_root / "alice" / "key-auth-progress").read_text(
            encoding="utf-8",
        ) == expected_progress

        shutil.rmtree(makers_root)
        sync_makers_projection(
            database_connection,
            CATALOG,
            MakersProjectionOptions(makers_root=makers_root, projected_at=PROJECTED_AT),
        )
        assert (makers_root / "alice" / "key-auth-progress").read_text(
            encoding="utf-8",
        ) == expected_progress


def test_makers_projection_rebuilds_deleted_content_from_package(
    migrated_database_path: Path,
    temporary_path: Path,
) -> None:
    """Deleting projected curriculum content is repairable from packaged files."""
    makers_root = temporary_path / "makers"
    documents_root = temporary_path / "docs"
    with connect_database(migrated_database_path) as database_connection:
        _write_projection_state(database_connection)
        sync_makers_projection(
            database_connection,
            CATALOG,
            MakersProjectionOptions(makers_root=makers_root, projected_at=PROJECTED_AT),
        )

        shutil.rmtree(documents_root)

        sync_makers_projection(
            database_connection,
            CATALOG,
            MakersProjectionOptions(makers_root=makers_root, projected_at=PROJECTED_AT),
        )

        assert (
            (documents_root / QUEST_CONTENT_PATH)
            .read_text(
                encoding="utf-8",
            )
            .startswith("# Prove the shell is alive\n")
        )


def test_makers_projection_publishes_open_references_and_gates_coursework(
    migrated_database_path: Path,
    temporary_path: Path,
) -> None:
    """Reference cards stay open while sessions and quests follow the release."""
    makers_root = temporary_path / "makers"
    documents_root = temporary_path / "docs"
    (documents_root / "stale.md").parent.mkdir(parents=True)
    (documents_root / "stale.md").write_text("stale\n", encoding="utf-8")

    with connect_database(migrated_database_path) as database_connection:
        sync_makers_projection(
            database_connection,
            CATALOG,
            MakersProjectionOptions(makers_root=makers_root, projected_at=PROJECTED_AT),
        )

        assert (documents_root / "README.md").read_text(encoding="utf-8") == (
            "# Linux Foundations\n\n"
            "Session material will be published when the first session begins.\n"
            "\n## Reference Cards\n\n- [Commands](commands/README.md)\n"
            "- [Concepts](concepts/README.md)\n- [Guides](guides/docs-map.md)\n"
        )
        assert "(tmux.md)" in (documents_root / "commands" / "README.md").read_text(
            encoding="utf-8"
        )
        assert "### Go Deeper After S03" in (documents_root / "concepts" / "README.md").read_text(
            encoding="utf-8"
        )
        assert find_missing_doc_references(documents_root) == []
    assert (documents_root / "commands" / "tmux.md").exists()
    assert (documents_root / "concepts" / "terminal-multiplexing.md").exists()
    assert (documents_root / "guides" / "docs-map.md").exists()
    assert (documents_root / "mentors" / "commands.md").exists()
    assert not (documents_root / "sessions").exists()
    assert not (documents_root / "quests").exists()
    assert not (documents_root / "stale.md").exists()

    with connect_database(migrated_database_path) as database_connection:
        upsert_course_release(
            database_connection,
            CourseRelease(
                course_id=CATALOG.course.id,
                session_reached="S1",
                released_at=PROJECTED_AT,
            ),
        )
        sync_makers_projection(
            database_connection,
            CATALOG,
            MakersProjectionOptions(makers_root=makers_root, projected_at=PROJECTED_AT),
        )

    course_index = (documents_root / "README.md").read_text(encoding="utf-8")
    assert "S1: First contact" in course_index
    assert all(
        index_link in course_index
        for index_link in (
            "- [Commands](commands/README.md)",
            "- [Concepts](concepts/README.md)",
            "- [Guides](guides/docs-map.md)",
            "- [Quests](quests/README.md)",
        )
    )
    assert (documents_root / "commands" / "tmux.md").exists()
    assert (documents_root / "concepts" / "terminal-multiplexing.md").exists()
    assert (documents_root / S01_SELF_STUDY_PATH).exists()
    assert (documents_root / QUEST_CONTENT_PATH).exists()
    assert not (documents_root / "sessions" / "S02").exists()
    assert not (documents_root / "quests" / "build-playground.md").exists()


def test_makers_projection_keeps_non_students_without_rank(
    migrated_database_path: Path,
    temporary_path: Path,
) -> None:
    """Course participants retain progress files without joining the ranking."""
    makers_root = temporary_path / "makers"
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, "mentor", "2026-07-18T09:00:00Z", rank_eligible=False)
        add_score_entry(
            database_connection,
            _score_entry("mentor", 25, "prove-shell-alive", "2026-07-19T09:00:00Z"),
        )
        sync_makers_projection(
            database_connection,
            CATALOG,
            MakersProjectionOptions(makers_root=makers_root, projected_at=PROJECTED_AT),
        )

    assert (makers_root / "mentor" / "score").read_text(encoding="utf-8") == "25\n"
    assert not (makers_root / "mentor" / "rank").exists()


def test_makers_projection_rejects_concurrent_sync(
    migrated_database_path: Path,
    temporary_path: Path,
) -> None:
    """A held makers-root lock prevents a second sync from writing or cleaning."""
    makers_root = temporary_path / "makers"
    _write_stale_files(makers_root)
    with connect_database(migrated_database_path) as database_connection:
        _write_projection_state(database_connection)
        with (
            _held_sync_lock(makers_root),
            pytest.raises(
                MakersProjectionError,
                match="already in progress",
            ),
        ):
            sync_makers_projection(
                database_connection,
                CATALOG,
                MakersProjectionOptions(
                    makers_root=makers_root,
                    projected_at=PROJECTED_AT,
                ),
            )

        assert (makers_root / "ghost").exists()
        assert get_projection_version(database_connection, MAKERS_PROJECTION_NAME) is None

        result = sync_makers_projection(
            database_connection,
            CATALOG,
            MakersProjectionOptions(makers_root=makers_root, projected_at=PROJECTED_AT),
        )

        assert result.learner_count == 2
        assert not (makers_root / "ghost").exists()


def test_makers_projection_uses_unique_destination_local_temp_paths(
    migrated_database_path: Path,
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Projection writes use unique temp names beside the destination file."""
    makers_root = temporary_path / "makers"

    def fail_replace(source_path: Path, target_path: str | Path) -> Path:
        raise OSError(f"simulated replace failure: {source_path} -> {target_path}")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with connect_database(migrated_database_path) as database_connection:
        _write_projection_state(database_connection)

        def write_projection_with_failed_replace() -> None:
            with pytest.raises(OSError, match="simulated replace failure"):
                sync_makers_projection(
                    database_connection,
                    CATALOG,
                    MakersProjectionOptions(
                        makers_root=makers_root,
                        projected_at=PROJECTED_AT,
                    ),
                )

        write_projection_with_failed_replace()
        write_projection_with_failed_replace()

    projection_temporary_paths = sorted(makers_root.rglob(".maker-guide-projection-*.*.tmp"))

    assert len(projection_temporary_paths) == 2
    assert (
        len(
            {
                projection_temporary_path.parent
                for projection_temporary_path in projection_temporary_paths
            }
        )
        == 1
    )


def test_makers_projection_rejects_malformed_projection_outbox_before_writing(
    migrated_database_path: Path,
    temporary_path: Path,
) -> None:
    """Projection sync validates queued projection payloads before file side effects."""
    makers_root = temporary_path / "makers"
    with connect_database(migrated_database_path) as database_connection:
        _write_projection_state(database_connection)
        database_connection.execute(
            """
            insert into outbox_items (kind, status, created_at, processed_at, payload_json)
            values (?, ?, ?, ?, ?)
            """,
            (
                PROJECTION_OUTBOX_KIND,
                PENDING_OUTBOX_STATUS,
                PROJECTED_AT,
                None,
                dump_json({"handle": "alice", "course_id": CATALOG.course.id}),
            ),
        )

        with pytest.raises(MakersProjectionError, match="projection outbox payload"):
            sync_makers_projection(
                database_connection,
                CATALOG,
                MakersProjectionOptions(makers_root=makers_root, projected_at=PROJECTED_AT),
            )

        assert get_projection_version(database_connection, MAKERS_PROJECTION_NAME) is None
        assert not (makers_root / "alice").exists()


def test_makers_projection_fsync_failure_prevents_outbox_processing(
    migrated_database_path: Path,
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Filesystem durability failures abort before SQLite processed state is written."""
    makers_root = temporary_path / "makers"

    def fail_fsync(file_descriptor: int) -> None:
        raise OSError(f"simulated fsync failure for {file_descriptor}")

    monkeypatch.setattr(makers_projection.os, "fsync", fail_fsync)
    with connect_database(migrated_database_path) as database_connection:
        _write_projection_state(database_connection)
        enqueue_outbox_item(
            database_connection,
            _outbox_item(kind=PROJECTION_OUTBOX_KIND, created_at="2026-07-25T08:58:00Z"),
        )

        with pytest.raises(OSError, match="simulated fsync failure"):
            sync_makers_projection(
                database_connection,
                CATALOG,
                MakersProjectionOptions(makers_root=makers_root, projected_at=PROJECTED_AT),
            )

        assert get_projection_version(database_connection, MAKERS_PROJECTION_NAME) is None
        assert [
            outbox_item.kind
            for outbox_item in list_retryable_outbox_items_by_kind(
                database_connection,
                PROJECTION_OUTBOX_KIND,
                10,
            )
        ] == [PROJECTION_OUTBOX_KIND]


def test_makers_projection_fsyncs_parent_directory_after_replace(
    migrated_database_path: Path,
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Projected file renames are followed by parent directory fsync."""
    makers_root = temporary_path / "makers"
    replaced_parent_paths: list[Path] = []
    fsynced_directory_paths: list[Path] = []
    original_replace = Path.replace

    def recording_replace(source_path: Path, target_path: str | Path) -> Path:
        replaced_parent_paths.append(Path(target_path).parent)
        return original_replace(source_path, target_path)

    def record_fsync_directory(path: Path) -> None:
        fsynced_directory_paths.append(path)

    monkeypatch.setattr(Path, "replace", recording_replace)
    monkeypatch.setattr(makers_projection, "_fsync_directory", record_fsync_directory)
    with connect_database(migrated_database_path) as database_connection:
        _write_projection_state(database_connection)
        sync_makers_projection(
            database_connection,
            CATALOG,
            MakersProjectionOptions(makers_root=makers_root, projected_at=PROJECTED_AT),
        )

    assert replaced_parent_paths
    for replaced_parent_path in replaced_parent_paths:
        assert replaced_parent_path in fsynced_directory_paths


def test_makers_projection_fsyncs_parent_directory_after_stale_removal(
    migrated_database_path: Path,
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stale file and directory removals are followed by parent directory fsync."""
    makers_root = temporary_path / "makers"
    _write_stale_files(makers_root)
    fsynced_directory_paths: list[Path] = []

    def record_fsync_directory(path: Path) -> None:
        fsynced_directory_paths.append(path)

    monkeypatch.setattr(makers_projection, "_fsync_directory", record_fsync_directory)
    with connect_database(migrated_database_path) as database_connection:
        _write_projection_state(database_connection)
        sync_makers_projection(
            database_connection,
            CATALOG,
            MakersProjectionOptions(makers_root=makers_root, projected_at=PROJECTED_AT),
        )

    assert not (makers_root / "ghost").exists()
    assert not (makers_root / "alice" / "stale").exists()
    assert makers_root in fsynced_directory_paths
    assert makers_root / "alice" in fsynced_directory_paths


@pytest.mark.parametrize(
    "relative_directory",
    [
        Path("alice"),
        Path("alice/solves"),
        Path("alice/adoptions"),
        Path("alice/tracks"),
    ],
)
def test_makers_projection_rejects_symlinked_projection_directories(
    migrated_database_path: Path,
    temporary_path: Path,
    relative_directory: Path,
) -> None:
    """Projection sync does not follow pre-existing symlink directories."""
    makers_root = temporary_path / "makers"
    symlink_target = temporary_path / "target"
    (makers_root / relative_directory).parent.mkdir(parents=True, exist_ok=True)
    symlink_target.mkdir()
    (makers_root / relative_directory).symlink_to(symlink_target, target_is_directory=True)
    with connect_database(migrated_database_path) as database_connection:
        _write_projection_state(database_connection)

        with pytest.raises(MakersProjectionError, match="unsafe symlinked projection directory"):
            sync_makers_projection(
                database_connection,
                CATALOG,
                MakersProjectionOptions(makers_root=makers_root, projected_at=PROJECTED_AT),
            )

    assert not (symlink_target / "rank").exists()
    assert not (symlink_target / "lockouts").exists()


def test_makers_projection_rejects_legacy_reserved_handle(
    migrated_database_path: Path,
    temporary_path: Path,
) -> None:
    """Legacy rows cannot collide with projection-internal lock names."""
    makers_root = temporary_path / "makers"
    with connect_database(migrated_database_path) as database_connection:
        database_connection.execute(
            """
            insert into learners (handle, joined_at, tagline, created_at)
            values (?, ?, ?, ?)
            """,
            (".sync.lock", "2026-07-18T09:00:00Z", None, "2026-07-18T09:00:00Z"),
        )
        upsert_membership(
            database_connection,
            CohortMembership(
                handle=".sync.lock",
                course_id=CATALOG.course.id,
                joined_at="2026-07-18T09:00:00Z",
            ),
        )
        upsert_course_release(
            database_connection,
            CourseRelease(
                course_id=CATALOG.course.id,
                session_reached="S2",
                released_at="2026-07-18T09:00:00Z",
            ),
        )

        with pytest.raises(MakersProjectionError, match="unsafe projection path component"):
            sync_makers_projection(
                database_connection,
                CATALOG,
                MakersProjectionOptions(makers_root=makers_root, projected_at=PROJECTED_AT),
            )


def test_makers_projection_record_write_is_nested_transaction_safe(
    migrated_database_path: Path,
    temporary_path: Path,
) -> None:
    """Projection version and outbox processed state roll back with an outer transaction."""
    makers_root = temporary_path / "makers"
    with connect_database(migrated_database_path) as database_connection:
        _write_projection_state(database_connection)
        enqueue_outbox_item(
            database_connection,
            _outbox_item(kind=PROJECTION_OUTBOX_KIND, created_at="2026-07-25T08:58:00Z"),
        )
        database_connection.execute(
            "update outbox_items set status = 'failed' where kind = ?",
            (PROJECTION_OUTBOX_KIND,),
        )
        with pytest.raises(RuntimeError, match="rollback outer transaction"):
            _sync_makers_projection_then_raise(database_connection, makers_root)

        assert get_projection_version(database_connection, MAKERS_PROJECTION_NAME) is None
        assert [
            outbox_item.kind
            for outbox_item in list_retryable_outbox_items_by_kind(
                database_connection,
                PROJECTION_OUTBOX_KIND,
                10,
            )
        ] == [PROJECTION_OUTBOX_KIND]


def _sync_makers_projection_then_raise(
    database_connection: sqlite3.Connection,
    makers_root: Path,
) -> None:
    with transaction(database_connection):
        sync_makers_projection(
            database_connection,
            CATALOG,
            MakersProjectionOptions(makers_root=makers_root, projected_at=PROJECTED_AT),
        )
        raise RuntimeError("rollback outer transaction")


def _write_stale_files(makers_root: Path) -> None:
    (makers_root / "alice").mkdir(parents=True)
    (makers_root / "alice" / "stale").write_text("stale\n", encoding="utf-8")
    (makers_root / "ghost").write_text("stale\n", encoding="utf-8")


@contextmanager
def _held_sync_lock(makers_root: Path) -> Generator[None]:
    makers_root.mkdir(parents=True, exist_ok=True)
    with (makers_root / ".sync.lock").open("a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _write_projection_state(database_connection: sqlite3.Connection) -> None:
    _write_member(database_connection, "alice", "2026-07-18T09:00:00Z")
    _write_member(database_connection, "bob", "2026-07-18T09:05:00Z")
    add_score_entry(
        database_connection,
        _score_entry("alice", 25, "prove-shell-alive", "2026-07-19T09:00:00Z"),
    )
    add_score_entry(
        database_connection,
        _score_entry("bob", 100, "prove-shell-alive", "2026-07-19T09:00:00Z"),
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
    upsert_course_release(
        database_connection,
        CourseRelease(
            course_id=CATALOG.course.id,
            session_reached="S2",
            released_at=joined_at,
        ),
    )


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


def _outbox_item(kind: str, created_at: str) -> OutboxItem:
    match kind:
        case matched_kind if matched_kind == PROJECTION_OUTBOX_KIND:
            return projection_outbox_item(
                handle="alice",
                course_id=CATALOG.course.id,
                created_at=created_at,
                reason="enrollment",
            )
        case _:
            return OutboxItem(
                id=None,
                kind=kind,
                status=PENDING_OUTBOX_STATUS,
                created_at=created_at,
                processed_at=None,
                payload={"handle": "alice", "course_id": CATALOG.course.id},
            )
