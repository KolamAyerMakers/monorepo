"""Tests for shared chat handling."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path
from textwrap import dedent
from typing import cast

import pytest

from maker_guide.chat.contract import (
    CHAT_INPUT_TOO_LONG_TEXT,
    DEFAULT_CHAT_MAX_INPUT_CHARS,
    ChatDependencies,
    ChatRequest,
    CliChatContext,
    IrcChatContext,
)
from maker_guide.chat.service import handle_chat_request
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.llm_tutor import (
    AnswerComponentAnalysis,
    AnswerInterpretation,
    AnswerInterpretationRequest,
    AnswerInterpreter,
    AnswerVerdict,
    TutorClient,
    TutorError,
    TutorRequest,
    TutorResponse,
)
from maker_guide.progress.models import CourseReleaseInput
from maker_guide.progress.service import release_course
from maker_guide.repositories.audit_event import (
    AuditEvent,
    append_audit_event,
    list_unexported_audit_events,
)
from maker_guide.repositories.cohort_membership import CohortMembership, upsert_membership
from maker_guide.repositories.command_observation import (
    CommandObservation,
    add_command_observation,
)
from maker_guide.repositories.course_release import CourseRelease, upsert_course_release
from maker_guide.repositories.group_grant import list_group_grants
from maker_guide.repositories.help_interaction import (
    HelpInteraction,
    add_help_interaction,
    list_recent_help_interactions,
)
from maker_guide.repositories.helpers import RepositoryError, connect_database, load_json
from maker_guide.repositories.learner import Learner, upsert_learner
from maker_guide.repositories.llm_audit_log import (
    LlmAuditLog,
    append_llm_audit_log,
    list_llm_audit_logs,
)
from maker_guide.repositories.outbox_item import list_pending_outbox_items
from maker_guide.repositories.quest_assignment import (
    QuestAssignment,
    assign_quest,
    list_assignments,
)
from maker_guide.repositories.quest_completion import QuestCompletion, get_quest_completion
from maker_guide.repositories.quest_completion import complete_quest as write_quest_completion
from maker_guide.repositories.score_ledger import (
    ScoreLedgerEntry,
    add_score_entry,
    total_score_for_course,
)
from maker_guide.repositories.session_objective_completion import (
    SessionObjectiveCompletion,
    complete_session_objective,
    list_completed_objective_ids,
)
from maker_guide.validation_paths import UnixAccount, UnixAccountLookup, lookup_unix_account

FREEFORM_TUTOR_DISABLED_TEXT = (
    dedent(
        """\
    I can't do open-ended tutoring here yet. Run `guide now` for your current quest,
    `guide check` when you've tried it, or `guide answer 'your answer'` when the
    quest asks a question.
    """,
    )
    .replace("\n", " ")
    .strip()
)
PROVE_SHELL_QUEST_DOC_PATH = "/docs/quests/prove-shell-alive.md"


def test_handle_chat_request_builds_snapshot_and_records_help(
    migrated_database_path: Path,
) -> None:
    """Shared chat handling resolves identity, snapshots state, and records help."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        add_score_entry(
            database_connection,
            ScoreLedgerEntry(
                id=None,
                handle="alice",
                course_id=CATALOG.course.id,
                amount=500,
                reason="quest_completed",
                related_type="quest",
                related_id="prove-shell-alive",
                created_at="2026-07-19T09:00:00Z",
            ),
        )

        response = handle_chat_request(
            ChatRequest(
                context=IrcChatContext(
                    nickname="alice",
                    target="#kolam",
                    reply_target="#kolam",
                ),
                visibility="public",
                text="hello",
            ),
            ChatDependencies(
                database_connection=database_connection,
                catalog=CATALOG,
                bot_name="guide-test",
                timestamp_factory=lambda: "2026-07-19T09:01:00Z",
            ),
        )

        assert response.text == FREEFORM_TUTOR_DISABLED_TEXT
        assert response.learner_snapshot.handle == "alice"
        assert response.learner_snapshot.score == 500
        assert response.learner_snapshot.tier == "apprentice"
        assert response.learner_snapshot.current_session == "S1"
        assert response.learner_snapshot.pending_quests == ("prove-shell-alive",)
        assert [
            interaction.question
            for interaction in list_recent_help_interactions(database_connection, "alice", 10)
        ] == ["hello"]


def test_snapshot_prioritizes_current_session_before_incomplete_assignment(
    migrated_database_path: Path,
) -> None:
    """Snapshots use the same current-session-first quest priority."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        assign_quest(
            database_connection,
            QuestAssignment(
                id=None,
                handle="alice",
                course_id=CATALOG.course.id,
                quest_id="prove-shell-alive",
                assigned_at="2026-07-19T09:00:00Z",
                source="chat",
            ),
        )
        upsert_course_release(
            database_connection,
            CourseRelease(
                course_id=CATALOG.course.id,
                session_reached="S2",
                released_at="2026-07-25T09:00:00Z",
            ),
        )

        response = handle_chat_request(
            _chat_request("progress"),
            _chat_dependencies(database_connection),
        )

        assert response.learner_snapshot.pending_quests == (
            "build-playground",
            "prove-shell-alive",
        )


def test_handle_chat_request_rejects_oversized_public_input(
    migrated_database_path: Path,
) -> None:
    """Oversized public chat input is rejected before help interaction storage."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)

        response = handle_chat_request(
            _chat_request("x" * (DEFAULT_CHAT_MAX_INPUT_CHARS + 1)),
            _chat_dependencies(database_connection),
        )

        assert response.text == CHAT_INPUT_TOO_LONG_TEXT
        assert list_recent_help_interactions(database_connection, "alice", 10) == []


def test_handle_chat_request_rejects_oversized_private_input_before_tutor(
    migrated_database_path: Path,
) -> None:
    """Oversized private chat input does not reach tutor or audit persistence."""
    tutor_client = _RecordingTutorClient("should not be used")
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)

        response = handle_chat_request(
            _private_chat_request("x" * (DEFAULT_CHAT_MAX_INPUT_CHARS + 1)),
            _chat_dependencies(database_connection, tutor_client=tutor_client),
        )

        assert response.text == CHAT_INPUT_TOO_LONG_TEXT
        assert tutor_client.requests == []
        assert list_llm_audit_logs(database_connection, "alice", limit=10) == []
        assert list_recent_help_interactions(database_connection, "alice", 10) == []


def test_today_alias_displays_current_objective_without_assigning_quest(
    migrated_database_path: Path,
) -> None:
    """Today remains a compatibility alias for the display-only now flow."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)

        response = handle_chat_request(
            _chat_request("today"),
            _chat_dependencies(database_connection),
        )

        assert response.text.startswith(
            "Current session objective: Confirm that your shell is working",
        )
        assert list_assignments(database_connection, "alice", CATALOG.course.id) == []
        assert response.learner_snapshot.pending_quests == ("prove-shell-alive",)


def test_progress_reports_recorded_state_without_assigning_work(
    migrated_database_path: Path,
) -> None:
    """Progress reports the current learner state without mutating it."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)

        response = handle_chat_request(
            _chat_request("progress"),
            _chat_dependencies(database_connection),
        )

        assert response.text == (
            "Progress:\n"
            "Session: S1\n"
            "Score: 0\n"
            "Tier: newcomer\n"
            "Objectives completed: 1\n"
            "Quests completed: 0\n"
            "Current objective: Confirm that your shell is working (S1)\n"
            "Next: guide now"
        )
        assert list_assignments(database_connection, "alice", CATALOG.course.id) == []


def test_progress_and_tutor_support_enrollment_before_first_release(
    migrated_database_path: Path,
) -> None:
    """Read-only chat remains available before any course session is released."""
    tutor_client = _RecordingTutorClient("Wait for the first session.")
    with connect_database(migrated_database_path) as database_connection:
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

        progress_response = handle_chat_request(
            _chat_request("progress"),
            _chat_dependencies(database_connection),
        )
        tutor_response = handle_chat_request(
            _private_chat_request("when do we start?"),
            _chat_dependencies(database_connection, tutor_client=tutor_client),
        )

    assert "Session: Not available yet" in progress_response.text
    assert tutor_response.text == "Wait for the first session."
    assert tutor_client.requests[0].context.current_objective is None
    assert tutor_client.requests[0].context.quests == ()


def test_now_displays_current_prompt_without_progress_side_effects(
    migrated_database_path: Path,
) -> None:
    """Now displays an incomplete objective without validation or quest assignment."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)

        response = handle_chat_request(
            _chat_request("now"),
            _chat_dependencies(database_connection),
        )

        assert response.text.startswith(
            "Current session objective: Confirm that your shell is working",
        )
        assert _attempt_count(database_connection) == 0
        assert total_score_for_course(database_connection, "alice", CATALOG.course.id) == 0
        assert (
            get_quest_completion(
                database_connection, "alice", CATALOG.course.id, "prove-shell-alive"
            )
            is None
        )
        assert list_assignments(database_connection, "alice", CATALOG.course.id) == []
        assert response.learner_snapshot.pending_quests == ("prove-shell-alive",)


def test_session_objective_command_evidence_starts_at_release_boundary(
    migrated_database_path: Path,
) -> None:
    """Commands before release do not count, while commands at release do."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        for command in ("whoami", "date", "uptime"):
            add_command_observation(
                database_connection,
                _command_observation(command, observed_at="2026-07-18T08:59:00Z"),
            )

        before_start_response = handle_chat_request(
            _chat_request("check"),
            _chat_dependencies(database_connection, timestamp="2026-07-18T09:00:00Z"),
        )
        for command in ("whoami", "date", "uptime"):
            add_command_observation(
                database_connection,
                _command_observation(command, observed_at="2026-07-18T09:00:00Z"),
            )
        after_start_response = handle_chat_request(
            _chat_request("check"),
            _chat_dependencies(database_connection, timestamp="2026-07-18T09:01:00Z"),
        )

    assert before_start_response.text.startswith(
        "Current session objective: Confirm that your shell is working",
    )
    assert after_start_response.text.startswith(
        "Current session objective: Navigate and inspect your home directory",
    )


def test_session_objective_accepts_commands_before_scheduled_session_start(
    migrated_database_path: Path,
) -> None:
    """Early cohort placement does not discard otherwise fresh objective evidence."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, released_at="2026-07-15T14:27:00Z")
        for command in ("whoami", "date", "uptime"):
            add_command_observation(
                database_connection,
                _command_observation(command, observed_at="2026-07-15T14:28:00Z"),
            )

        response = handle_chat_request(
            _chat_request("check"),
            _chat_dependencies(database_connection, timestamp="2026-07-15T14:29:00Z"),
        )

    assert response.text.startswith(
        "Current session objective: Navigate and inspect your home directory",
    )


def test_s1_irc_join_audit_completes_first_rewarded_objective(
    migrated_database_path: Path,
) -> None:
    """Joining the course channel completes S1's first objective and awards its score."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, joined_irc=False)
        append_audit_event(
            database_connection,
            AuditEvent(
                event_type="irc_channel_joined",
                handle="alice",
                source="test",
                created_at="2026-07-19T09:00:00Z",
                payload={"channel": "#lf2607"},
            ),
        )

        response = handle_chat_request(
            _chat_request("check"),
            _chat_dependencies(database_connection, timestamp="2026-07-19T09:01:00Z"),
        )

        assert response.text.startswith(
            "Current session objective: Confirm that your shell is working",
        )
        assert total_score_for_course(database_connection, "alice", CATALOG.course.id) == 55


@pytest.mark.parametrize("command", ["ls", "ls -la ~", "ls public_html"])
def test_session_objective_accepts_any_ls_command(
    migrated_database_path: Path,
    command: str,
) -> None:
    """The home-directory objective accepts any ls invocation."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        for prerequisite_command in ("whoami", "date", "uptime"):
            add_command_observation(
                database_connection,
                _command_observation(prerequisite_command),
            )
        handle_chat_request(
            _chat_request("check"),
            _chat_dependencies(database_connection),
        )
        add_command_observation(database_connection, _command_observation(command))

        response = handle_chat_request(
            _chat_request("check"),
            _chat_dependencies(database_connection),
        )

    assert response.text.startswith("Current session objective: Read a manual page")


def test_session_objective_reports_missing_command_from_composite_evidence(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """An existing page reports the missing build command rather than generic feedback."""
    learner_home = tmp_path / "alice"
    public_html_path = learner_home / "public_html"
    public_html_path.mkdir(parents=True)
    (public_html_path / "index.html").write_text("<h1>Alice</h1>\n", encoding="utf-8")

    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        for objective_id in ("prove-shell-alive", "count-home-entries", "read-man-ls"):
            complete_session_objective(
                database_connection,
                SessionObjectiveCompletion(
                    handle="alice",
                    course_id=CATALOG.course.id,
                    session_id="S1",
                    objective_id=objective_id,
                    completed_at="2026-07-19T09:00:00Z",
                    evidence_json="{}",
                ),
            )
        add_command_observation(database_connection, _command_observation("ls public_html"))

        response = handle_chat_request(
            _chat_request("check"),
            _chat_dependencies(database_connection, account_lookup=_account_lookup(learner_home)),
        )

    assert response.text.startswith("Current session objective: Ship your first page")
    assert "I need to see this command before I can verify the objective: `build-website`" in (
        response.text
    )
    assert "I cannot verify that yet" not in response.text


def test_failed_session_objective_check_writes_operational_audit(
    migrated_database_path: Path,
) -> None:
    """Objective failures retain evidence and operational metadata without attempts."""

    def missing_account(handle: str) -> UnixAccount | None:
        del handle
        return None

    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        for objective_id in ("prove-shell-alive", "count-home-entries", "read-man-ls"):
            complete_session_objective(
                database_connection,
                SessionObjectiveCompletion(
                    handle="alice",
                    course_id=CATALOG.course.id,
                    session_id="S1",
                    objective_id=objective_id,
                    completed_at="2026-07-18T09:00:00Z",
                    evidence_json="{}",
                ),
            )
        add_command_observation(database_connection, _command_observation("build-website"))

        response = handle_chat_request(
            _chat_request("check"),
            _chat_dependencies(database_connection, account_lookup=missing_account),
        )
        audit_events = list_unexported_audit_events(database_connection, 10)

    assert response.text.startswith("Current session objective: Ship your first page")
    failure_event = next(
        event for event in audit_events if event.event_type == "session_objective_validation_failed"
    )
    assert failure_event.payload["session_id"] == "S1"
    assert failure_event.payload["objective_id"] == "build-first-site"
    assert failure_event.payload["failure_reason"] == "unknown-user"
    evidence = cast("dict[str, object]", failure_event.payload["evidence"])
    assert evidence["validation_type"] == "all_of"
    assert evidence["failure_reason"] == "unknown-user"
    assert next(
        event.payload
        for event in audit_events
        if event.event_type == "operational_validation_failed"
    ) == {
        "course_id": CATALOG.course.id,
        "failure_reason": "unknown-user",
        "objective_id": "build-first-site",
        "session_id": "S1",
    }


def test_now_does_not_announce_or_complete_session_objective(migrated_database_path: Path) -> None:
    """Now does not validate objectives or award their score and tier effects."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        add_score_entry(
            database_connection,
            ScoreLedgerEntry(
                id=None,
                handle="alice",
                course_id=CATALOG.course.id,
                amount=445,
                reason="test",
                related_type="test",
                related_id="before-objective",
                created_at="2026-07-19T08:00:00Z",
            ),
        )
        for command in ("whoami", "date", "uptime"):
            add_command_observation(database_connection, _command_observation(command))

        response = handle_chat_request(
            _chat_request("now"),
            _chat_dependencies(database_connection),
        )

    assert response.public_announcements == ()
    assert response.text.startswith(
        "Current session objective: Confirm that your shell is working",
    )
    assert total_score_for_course(database_connection, "alice", CATALOG.course.id) == 445


def test_session_objective_completion_returns_tier_announcement(
    migrated_database_path: Path,
) -> None:
    """A guide check preserves the public announcement from an objective promotion."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        add_score_entry(
            database_connection,
            ScoreLedgerEntry(
                id=None,
                handle="alice",
                course_id=CATALOG.course.id,
                amount=445,
                reason="test",
                related_type="test",
                related_id="before-objective",
                created_at="2026-07-18T08:00:00Z",
            ),
        )
        for command in ("whoami", "date", "uptime"):
            add_command_observation(database_connection, _command_observation(command))

        response = handle_chat_request(
            _chat_request("check"),
            _chat_dependencies(database_connection),
        )

    assert response.public_announcements == ("alice became an apprentice",)
    assert response.learner_snapshot.tier == "apprentice"


def test_quest_promotion_stays_in_private_learner_response(
    migrated_database_path: Path,
) -> None:
    """Quest promotions inform the learner without requesting a public broadcast."""
    request_context = CliChatContext(username="alice", terminal="/dev/pts/1")
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _complete_current_session_objectives(database_connection)
        add_score_entry(
            database_connection,
            ScoreLedgerEntry(
                id=None,
                handle="alice",
                course_id=CATALOG.course.id,
                amount=470,
                reason="test",
                related_type="test",
                related_id="before-quest",
                created_at="2026-07-19T08:00:00Z",
            ),
        )
        handle_chat_request(
            ChatRequest(context=request_context, visibility="private", text="now"),
            _chat_dependencies(database_connection, timestamp="2026-07-19T09:00:00Z"),
        )
        for command in ("whoami", "date", "uptime"):
            add_command_observation(
                database_connection,
                _command_observation(command, observed_at="2026-07-19T09:01:00Z"),
            )

        response = handle_chat_request(
            ChatRequest(context=request_context, visibility="private", text="check"),
            _chat_dependencies(database_connection, timestamp="2026-07-19T09:02:00Z"),
        )

    assert "New tier: Apprentice" in response.text
    assert response.public_announcements == ()


def test_now_does_not_complete_proven_quest(
    migrated_database_path: Path,
) -> None:
    """Now displays the current prompt even when practical evidence is already present."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _complete_current_session_objectives(database_connection)
        handle_chat_request(
            _chat_request("today"),
            _chat_dependencies(database_connection, timestamp="2026-07-19T09:00:00Z"),
        )
        for command in ("whoami", "date", "uptime"):
            add_command_observation(
                database_connection,
                _command_observation(command, observed_at="2026-07-19T09:01:00Z"),
            )

        response = handle_chat_request(
            _chat_request("now"),
            _chat_dependencies(database_connection, timestamp="2026-07-19T09:02:00Z"),
        )

        assert response.text.startswith("Today's quest: Prove the shell is alive")
        assert _attempt_count(database_connection) == 0
        assert response.learner_snapshot.completed_quests == ()
        assert response.learner_snapshot.pending_quests == ("prove-shell-alive",)


def test_now_does_not_validate_existing_evidence(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Now leaves existing objective and quest evidence untouched."""
    learner_home = tmp_path / "alice"
    public_html_path = learner_home / "public_html"
    public_html_path.mkdir(parents=True)
    (public_html_path / "index.html").write_text("<h1>Alice</h1>\n", encoding="utf-8")

    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        for command, observed_at in (
            ("whoami", "2026-07-19T09:00:00Z"),
            ("date", "2026-07-19T09:00:01Z"),
            ("uptime", "2026-07-19T09:00:02Z"),
            ("ls", "2026-07-19T09:00:03Z"),
            ("man ls", "2026-07-19T09:00:04Z"),
            ("build-website", "2026-07-19T09:00:05Z"),
        ):
            add_command_observation(
                database_connection,
                _command_observation(command, observed_at=observed_at),
            )

        response = handle_chat_request(
            _chat_request("now"),
            _chat_dependencies(
                database_connection,
                account_lookup=_account_lookup(learner_home),
                timestamp="2026-07-19T09:00:10Z",
            ),
        )

        assert response.text.startswith(
            "Current session objective: Confirm that your shell is working",
        )
        assert _attempt_count(database_connection) == 0
        assert response.learner_snapshot.completed_quests == ()


def test_now_shows_current_s2_objective_before_quest(
    migrated_database_path: Path,
) -> None:
    """The released session objective takes priority over current-session quests."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, session_reached="S2")
        assign_quest(
            database_connection,
            QuestAssignment(
                id=None,
                handle="alice",
                course_id=CATALOG.course.id,
                quest_id="prove-shell-alive",
                assigned_at="2026-07-19T09:00:00Z",
                source="test",
            ),
        )

        response = handle_chat_request(
            _chat_request("now"),
            _chat_dependencies(database_connection, timestamp="2026-07-25T09:00:00Z"),
        )

        assert response.text.startswith(
            "Current session objective: Connect with an SSH public key",
        )
        assert list_assignments(database_connection, "alice", CATALOG.course.id) == [
            QuestAssignment(
                id=1,
                handle="alice",
                course_id=CATALOG.course.id,
                quest_id="prove-shell-alive",
                assigned_at="2026-07-19T09:00:00Z",
                source="test",
            ),
        ]
        assert response.learner_snapshot.pending_quests == (
            "build-playground",
            "prove-shell-alive",
        )


def test_check_intent_prioritizes_current_session_objective(
    migrated_database_path: Path,
) -> None:
    """Checks cannot bypass the current session's objective sequence."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)

        response = handle_chat_request(
            _chat_request("check my work"),
            _chat_dependencies(database_connection),
        )

        assert response.text.startswith(
            "Current session objective: Confirm that your shell is working",
        )
        assert "Today's quest:" not in response.text
        assert _attempt_count(database_connection) == 0
        assert list_assignments(database_connection, "alice", CATALOG.course.id) == []
        assert (
            get_quest_completion(
                database_connection,
                "alice",
                CATALOG.course.id,
                "prove-shell-alive",
            )
            is None
        )


def test_answer_intent_displays_current_session_objective_without_validation(
    migrated_database_path: Path,
) -> None:
    """Answers cannot bypass or validate a practical current session objective."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)

        response = handle_chat_request(
            _chat_request("answer whoami"),
            _chat_dependencies(database_connection),
        )

        assert response.text.startswith(
            "Current session objective: Confirm that your shell is working",
        )
        assert list_assignments(database_connection, "alice", CATALOG.course.id) == []


def test_answer_intent_validates_answer_bearing_session_objective(
    migrated_database_path: Path,
) -> None:
    """Conceptual objectives accept answers after their practical evidence exists."""
    tutor_client = _RecordingTutorClient("should not be used")
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, session_reached="S3")
        _complete_current_session_objectives(database_connection, "S1")
        _complete_current_session_objectives(database_connection, "S2")
        with database_connection:
            for objective in CATALOG.session("S3").objectives:
                if objective.id == "report-process-pair":
                    continue
                complete_session_objective(
                    database_connection,
                    SessionObjectiveCompletion(
                        handle="alice",
                        course_id=CATALOG.course.id,
                        session_id="S3",
                        objective_id=objective.id,
                        completed_at="2026-08-01T09:00:00Z",
                        evidence_json="{}",
                    ),
                )
        add_command_observation(
            database_connection,
            _command_observation(
                'ps -u "$USER" -o pid,comm,args',
                observed_at="2026-08-01T09:01:00Z",
            ),
        )

        response = handle_chat_request(
            ChatRequest(
                context=CliChatContext(username="alice", terminal="/dev/pts/1"),
                visibility="private",
                text=(
                    "A binary executable is a program file; a process is a running instance. "
                    "PID 4242, command bash."
                ),
            ),
            _chat_dependencies(
                database_connection,
                tutor_client=tutor_client,
                timestamp="2026-08-01T09:02:00Z",
            ),
        )

        assert response.text.startswith(
            "Answer accepted. Objective complete: Report a process ID and command.",
        )
        assert "Next:\n\nToday's quest: Count a stream" in response.text
        assert tutor_client.requests == []


@pytest.mark.parametrize(
    ("answer", "expected_feedback"),
    [
        (
            "stdout 1 stdin 0",
            "I can't connect that answer to the full idea yet.",
        ),
        (
            "stdout/1 stdin/0",
            "I can't connect that answer to the full idea yet.",
        ),
        (
            "cut stdout; wc stdin",
            "I can't connect that answer to the full idea yet.",
        ),
        (
            "cut never writes stdout and wc never reads stdin",
            "One part of that answer conflicts with the concept.",
        ),
    ],
)
def test_answer_intent_nudges_missing_pipe_associations(
    migrated_database_path: Path,
    answer: str,
    expected_feedback: str,
) -> None:
    """Pipe answers identify the association the learner still needs to provide."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, session_reached="S3")
        _complete_current_session_objectives(database_connection, "S2")
        complete_session_objective(
            database_connection,
            SessionObjectiveCompletion(
                handle="alice",
                course_id=CATALOG.course.id,
                session_id="S3",
                objective_id="separate-standard-streams",
                completed_at="2026-08-01T09:00:00Z",
                evidence_json="{}",
            ),
        )
        add_command_observation(
            database_connection,
            _command_observation(
                "cut -d: -f1 /etc/passwd | wc -l",
                observed_at="2026-08-01T09:01:00Z",
            ),
        )

        response = handle_chat_request(
            _chat_request(f"answer {answer}"),
            _chat_dependencies(database_connection, timestamp="2026-08-01T09:02:00Z"),
        )

    assert expected_feedback in response.text
    assert "I cannot verify that yet" not in response.text


def test_answer_intent_nudges_wrong_stderr_descriptor(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Descriptor answers identify the association the learner needs to correct."""
    learner_home = tmp_path / "alice"
    with connect_database(migrated_database_path) as database_connection:
        _prepare_combine_streams_objective(database_connection, learner_home)
        answer = "stderr is descriptor 1"

        response = handle_chat_request(
            _chat_request(f"answer {answer}"),
            _chat_dependencies(
                database_connection,
                account_lookup=_account_lookup(learner_home),
                timestamp="2026-08-01T09:02:00Z",
            ),
        )

    assert "One part of that answer conflicts with the concept." in response.text
    assert "What would you change?" in response.text
    assert "I cannot verify that yet" not in response.text


def test_answer_interpreter_tool_verdicts_gate_completion(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Semantic tool verdicts inform grading but deterministic code owns completion."""
    learner_home = tmp_path / "alice"
    with connect_database(migrated_database_path) as database_connection:
        _prepare_combine_streams_objective(database_connection, learner_home)
        contradicted_interpreter = _RecordingAnswerInterpreter(
            database_connection,
            (_component("stderr-descriptor", "contradicted", "descriptor 2 is stderr"),),
            feedback=(
                "You connected descriptor 2 with a standard stream. "
                "Which stream receives diagnostic messages?"
            ),
        )
        answer = "descriptor 2 is stderr"

        contradicted_response = handle_chat_request(
            _private_chat_request(f"answer {answer}"),
            _chat_dependencies(
                database_connection,
                account_lookup=_account_lookup(learner_home),
                answer_interpreter=contradicted_interpreter,
                timestamp="2026-08-01T09:02:00Z",
            ),
        )

        assert "Let's work through your answer:" in contradicted_response.text
        assert "Which stream receives diagnostic messages?" in contradicted_response.text
        assert "combine-and-copy-streams" not in list_completed_objective_ids(
            database_connection,
            "alice",
            CATALOG.course.id,
            "S3",
        )

        accepted_interpreter = _RecordingAnswerInterpreter(
            database_connection,
            tuple(
                _component(rubric.concept_id, "demonstrated", "correct")
                for rubric in contradicted_interpreter.requests[0].concept_rubrics
            ),
        )
        accepted_response = handle_chat_request(
            _private_chat_request("answer correct"),
            _chat_dependencies(
                database_connection,
                account_lookup=_account_lookup(learner_home),
                answer_interpreter=accepted_interpreter,
                timestamp="2026-08-01T09:03:00Z",
            ),
        )

        assert accepted_response.text.startswith(
            "Answer accepted. Objective complete: Identify descriptor 2's stream.",
        )
        assert "Next:\n\nCurrent session objective: Explain redirection order" in (
            accepted_response.text
        )
        assert "combine-and-copy-streams" in list_completed_objective_ids(
            database_connection,
            "alice",
            CATALOG.course.id,
            "S3",
        )
        assert [
            audit_log.status for audit_log in list_llm_audit_logs(database_connection, "alice", 10)
        ] == [
            "answer_interpreted",
            "answer_interpreted",
        ]
        assert len(contradicted_interpreter.requests) == 1
        assert len(accepted_interpreter.requests) == 1


def test_stale_answer_interpretation_is_not_applied_to_next_objective(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Concurrent progress invalidates semantic analysis prepared for the old target."""
    learner_home = tmp_path / "alice"
    with connect_database(migrated_database_path) as database_connection:
        _prepare_combine_streams_objective(database_connection, learner_home)

        def advance_progress() -> None:
            complete_session_objective(
                database_connection,
                SessionObjectiveCompletion(
                    handle="alice",
                    course_id=CATALOG.course.id,
                    session_id="S3",
                    objective_id="combine-and-copy-streams",
                    completed_at="2026-08-01T09:02:00Z",
                    evidence_json="{}",
                ),
            )
            database_connection.commit()

        interpreter = _RecordingAnswerInterpreter(
            database_connection,
            (_component("stderr-descriptor", "demonstrated", "correct"),),
            on_interpret=advance_progress,
        )

        response = handle_chat_request(
            _private_chat_request("answer correct"),
            _chat_dependencies(
                database_connection,
                account_lookup=_account_lookup(learner_home),
                answer_interpreter=interpreter,
                timestamp="2026-08-01T09:03:00Z",
            ),
        )

    assert response.text.startswith("Current session objective: Explain redirection order")
    assert "I still need" not in response.text


def test_answer_objective_explains_early_answer_and_check_transition(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Mixed objectives distinguish a correct answer, practical evidence, and completion."""
    learner_home = tmp_path / "alice"
    (learner_home / "playground").mkdir(parents=True)
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, session_reached="S3")
        _complete_current_session_objectives(database_connection, "S2")
        with database_connection:
            for objective in CATALOG.session("S3").objectives:
                if objective.id == "combine-and-copy-streams":
                    break
                complete_session_objective(
                    database_connection,
                    SessionObjectiveCompletion(
                        handle="alice",
                        course_id=CATALOG.course.id,
                        session_id="S3",
                        objective_id=objective.id,
                        completed_at="2026-08-01T09:00:00Z",
                        evidence_json="{}",
                    ),
                )
        interpreter = _RecordingAnswerInterpreter(
            database_connection,
            (_component("stderr-descriptor", "demonstrated", "fd 2 is stderr"),),
        )

        early_answer_response = handle_chat_request(
            _private_chat_request("answer fd 2 is stderr"),
            _chat_dependencies(
                database_connection,
                account_lookup=_account_lookup(learner_home),
                answer_interpreter=interpreter,
                timestamp="2026-08-01T09:01:00Z",
            ),
        )

        (learner_home / "playground" / "combined.txt").write_text(
            "date: output format: %F\n2026-08-01\n",
            encoding="utf-8",
        )
        add_command_observation(
            database_connection,
            _command_observation(
                "date --debug +%F 2>&1 | tee ~/playground/combined.txt | wc -l",
                observed_at="2026-08-01T09:02:00Z",
            ),
        )
        check_response = handle_chat_request(
            _private_chat_request("check"),
            _chat_dependencies(
                database_connection,
                account_lookup=_account_lookup(learner_home),
                timestamp="2026-08-01T09:03:00Z",
            ),
        )

    assert "Your answer is correct, but the practical step is still missing." in (
        early_answer_response.text
    )
    assert "send your answer once more to complete the objective" in early_answer_response.text
    assert "The practical evidence is ready. Now answer this question" in check_response.text
    assert "What stream is represented by descriptor 2?" in check_response.text


def test_releasing_s4_prioritizes_s4_before_unfinished_s3_objective(
    migrated_database_path: Path,
) -> None:
    """A new release supersedes unfinished objectives from earlier sessions."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, session_reached="S2")
        _complete_current_session_objectives(database_connection, "S2")
        release_course(
            database_connection,
            CATALOG,
            CourseReleaseInput(
                session_reached="S3",
                updated_at="2026-07-31T09:00:00Z",
                source="test",
            ),
        )
        complete_session_objective(
            database_connection,
            SessionObjectiveCompletion(
                handle="alice",
                course_id=CATALOG.course.id,
                session_id="S3",
                objective_id="separate-standard-streams",
                completed_at="2026-08-01T09:01:00Z",
                evidence_json="{}",
            ),
        )
        add_command_observation(
            database_connection,
            _command_observation(
                "cut -d: -f1 /etc/passwd | wc -l",
                observed_at="2026-07-31T09:01:00Z",
            ),
        )
        release_course(
            database_connection,
            CATALOG,
            CourseReleaseInput(
                session_reached="S4",
                updated_at="2026-08-08T09:00:00Z",
                source="test",
            ),
        )

        response = handle_chat_request(
            _chat_request("answer cut writes stdout (1) and wc reads stdin (0)"),
            _chat_dependencies(database_connection, timestamp="2026-08-08T09:01:00Z"),
        )

        assert response.text.startswith(
            "Current session objective: Read and change file permissions",
        )
        assert list_completed_objective_ids(
            database_connection,
            "alice",
            CATALOG.course.id,
            "S3",
        ) == frozenset({"separate-standard-streams"})
        assert list_assignments(database_connection, "alice", CATALOG.course.id) == []


def test_cli_bare_statement_reaches_tutor_during_practical_objective(
    migrated_database_path: Path,
) -> None:
    """A pending answer quest cannot steal free-form help from a practical objective."""
    tutor_client = _RecordingTutorClient("inspect stdout.txt and stderr.txt separately")
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _write_completed_quests(database_connection, ("prove-shell-alive",))

        response = handle_chat_request(
            ChatRequest(
                context=CliChatContext(username="alice", terminal="/dev/pts/1"),
                visibility="private",
                text="the stdout file is empty",
            ),
            _chat_dependencies(database_connection, tutor_client=tutor_client),
        )

        assert response.text == "inspect stdout.txt and stderr.txt separately"
        assert [request.message for request in tutor_client.requests] == [
            "the stdout file is empty"
        ]


def test_failed_check_lists_seen_and_missing_commands(migrated_database_path: Path) -> None:
    """Partial command evidence is reported exactly instead of contradicting freeform help."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _complete_current_session_objectives(database_connection)
        handle_chat_request(
            _chat_request("now"),
            _chat_dependencies(database_connection, timestamp="2026-07-19T09:01:00Z"),
        )
        add_command_observation(
            database_connection,
            _command_observation("whoami", observed_at="2026-07-19T09:02:00Z"),
        )

        response = handle_chat_request(
            _chat_request("check my work"),
            _chat_dependencies(database_connection, timestamp="2026-07-19T09:03:00Z"),
        )

        assert "Seen: `whoami`" in response.text
        assert "Missing: `date`, `uptime`" in response.text


def test_check_intent_completes_current_quest_from_command_observations(
    migrated_database_path: Path,
) -> None:
    """Passed deterministic checks complete quests through the progress service."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _complete_current_session_objectives(database_connection)
        handle_chat_request(
            _chat_request("today"),
            _chat_dependencies(database_connection, timestamp="2026-07-19T09:00:00Z"),
        )
        for command in ("whoami", "date", "uptime"):
            add_command_observation(
                database_connection,
                _command_observation(command, observed_at="2026-07-19T09:01:00Z"),
            )

        response = handle_chat_request(
            _chat_request("am I finished"),
            _chat_dependencies(database_connection, timestamp="2026-07-19T09:02:00Z"),
        )

        assert response.text == _completed_quest_text("Prove the shell is alive", 30)
        assert response.learner_snapshot.completed_quests == ("prove-shell-alive",)
        assert response.learner_snapshot.score == 30
        assert total_score_for_course(database_connection, "alice", CATALOG.course.id) == 30
        assert (
            get_quest_completion(
                database_connection,
                "alice",
                CATALOG.course.id,
                "prove-shell-alive",
            )
            is not None
        )
        assert {
            event.event_type for event in list_unexported_audit_events(database_connection, 10)
        } >= {
            "quest_attempted",
            "quest_completed",
            "score_awarded",
        }


def test_answer_does_not_validate_practical_quest(migrated_database_path: Path) -> None:
    """Answers leave practical quest validation to guide check."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _complete_current_session_objectives(database_connection)

        response = handle_chat_request(
            _chat_request("answer I ran the commands"),
            _chat_dependencies(database_connection),
        )

        assert response.text.startswith("Today's quest: Prove the shell is alive")
        assert _attempt_count(database_connection) == 0
        assert (
            get_quest_completion(
                database_connection,
                "alice",
                CATALOG.course.id,
                "prove-shell-alive",
            )
            is None
        )


def test_check_rolls_back_progress_when_help_logging_fails(
    migrated_database_path: Path,
) -> None:
    """Chat commits progress and help logging as one atomic request."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _complete_current_session_objectives(database_connection)
        handle_chat_request(
            _chat_request("today"),
            _chat_dependencies(database_connection, timestamp="2026-07-19T09:00:00Z"),
        )
        for command in ("whoami", "date", "uptime"):
            add_command_observation(
                database_connection,
                _command_observation(command, observed_at="2026-07-19T09:01:00Z"),
            )
        audit_event_count = len(list_unexported_audit_events(database_connection, 50))
        pending_outbox_count = len(list_pending_outbox_items(database_connection, 50))
        _block_help_interaction_inserts(database_connection)

        with pytest.raises(sqlite3.IntegrityError, match="help interaction insert blocked"):
            handle_chat_request(
                _chat_request("check my work"),
                _chat_dependencies(database_connection, timestamp="2026-07-19T09:02:00Z"),
            )

        assert _attempt_count(database_connection) == 0
        assert (
            get_quest_completion(
                database_connection,
                "alice",
                CATALOG.course.id,
                "prove-shell-alive",
            )
            is None
        )
        assert total_score_for_course(database_connection, "alice", CATALOG.course.id) == 0
        assert len(list_unexported_audit_events(database_connection, 50)) == audit_event_count
        assert len(list_pending_outbox_items(database_connection, 50)) == pending_outbox_count
        assert "check my work" not in _help_interaction_questions(database_connection)


def test_check_rolls_back_attempt_when_completion_fails_before_help_logging(
    migrated_database_path: Path,
) -> None:
    """A later progress failure rolls back earlier chat-owned writes."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _complete_current_session_objectives(database_connection)
        handle_chat_request(
            _chat_request("today"),
            _chat_dependencies(database_connection, timestamp="2026-07-19T09:00:00Z"),
        )
        for command in ("whoami", "date", "uptime"):
            add_command_observation(
                database_connection,
                _command_observation(command, observed_at="2026-07-19T09:01:00Z"),
            )
        _write_conflicting_score(database_connection, "prove-shell-alive")
        audit_event_count = len(list_unexported_audit_events(database_connection, 50))
        pending_outbox_count = len(list_pending_outbox_items(database_connection, 50))

        with pytest.raises(RepositoryError, match="conflicting score ledger entry"):
            handle_chat_request(
                _chat_request("check my work"),
                _chat_dependencies(database_connection, timestamp="2026-07-19T09:02:00Z"),
            )

        assert _attempt_count(database_connection) == 0
        assert (
            get_quest_completion(
                database_connection,
                "alice",
                CATALOG.course.id,
                "prove-shell-alive",
            )
            is None
        )
        assert total_score_for_course(database_connection, "alice", CATALOG.course.id) == 1
        assert len(list_unexported_audit_events(database_connection, 50)) == audit_event_count
        assert len(list_pending_outbox_items(database_connection, 50)) == pending_outbox_count
        assert "check my work" not in _help_interaction_questions(database_connection)


def test_now_shows_answer_question_for_interactive_current_quest(
    migrated_database_path: Path,
) -> None:
    """Today prompts for explicit answers when the current quest needs one."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _complete_current_session_objectives(database_connection)
        _complete_first_quest(database_connection)

        response = handle_chat_request(
            _chat_request("now"),
            _chat_dependencies(database_connection),
        )

        assert response.text.startswith("Today's quest: Name the system")
        assert "PRETTY_NAME value" in response.text
        assert "When ready, run: guide answer 'your answer'" in response.text
        assert _attempt_count(database_connection) == 1


def test_check_without_answer_returns_missing_answer_feedback_without_recording_attempt(
    migrated_database_path: Path,
) -> None:
    """Checking without an answer returns feedback without recording an attempt."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _complete_current_session_objectives(database_connection)
        _complete_first_quest(database_connection)

        response = handle_chat_request(
            _chat_request("check my work"),
            _chat_dependencies(database_connection),
        )

        assert response.text.startswith("Today's quest: Name the system")
        assert "When ready, run: guide answer 'your answer'" in response.text
        assert _attempt_count(database_connection) == 1


def test_answer_intent_records_raw_help_question_and_structured_evidence(
    migrated_database_path: Path,
) -> None:
    """Answer text is logged for debugging but not stored in validation evidence."""
    tutor_client = _RecordingTutorClient("should not be used")
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _complete_current_session_objectives(database_connection)
        _complete_first_quest(database_connection)

        response = handle_chat_request(
            _chat_request("answer Debian GNU/Linux"),
            _chat_dependencies(database_connection, tutor_client=tutor_client),
        )

        assert response.text == _completed_quest_text("Name the system", 60)
        assert tutor_client.requests == []
        attempt_record = _latest_attempt_record(database_connection)
        assert attempt_record[:2] == ("passed", None)
        evidence = load_json(attempt_record[2])
        assert evidence == {
            "answer_present": True,
            "contradicted_concept_count": 0,
            "contradicted_concept_ids": [],
            "expected_concept_count": 1,
            "failure_reason": None,
            "matched_concept_count": 1,
            "matched_concept_ids": ["debian-pretty-name"],
            "missing_concept_ids": [],
            "passed": True,
            "validation_type": "interactive_question",
        }
        assert "Debian" not in str(evidence)
        assert response.learner_snapshot.completed_quests == ("prove-shell-alive", "name-system")
        assert response.learner_snapshot.pending_quests == ("count-home-entries",)
        assert list_recent_help_interactions(database_connection, "alice", 1)[0].question == (
            "answer Debian GNU/Linux"
        )


def test_cli_answer_intent_uses_same_private_validation_flow(
    migrated_database_path: Path,
) -> None:
    """CLI answer requests use the shared answer flow and retain chat history."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _complete_current_session_objectives(database_connection)
        _complete_first_quest(database_connection)

        response = handle_chat_request(
            ChatRequest(
                context=CliChatContext(username="alice", terminal="/dev/pts/1"),
                visibility="private",
                text="answer Debian GNU/Linux",
            ),
            _chat_dependencies(database_connection),
        )

        assert response.text.startswith("Done.\n\nCompleted quest: Name the system")
        assert list_recent_help_interactions(database_connection, "alice", 1)[0].question == (
            "answer Debian GNU/Linux"
        )


def test_cli_bare_text_answers_interactive_quest_without_llm(
    migrated_database_path: Path,
) -> None:
    """Bare CLI answer text uses deterministic validation for answer quests."""
    tutor_client = _RecordingTutorClient("should not be used")
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _complete_current_session_objectives(database_connection)
        _complete_first_quest(database_connection)

        response = handle_chat_request(
            ChatRequest(
                context=CliChatContext(username="alice", terminal="/dev/pts/1"),
                visibility="private",
                text="pretty name is Debian GNU/Linux 13 (trixie)",
            ),
            _chat_dependencies(database_connection, tutor_client=tutor_client),
        )

        assert response.text == _completed_quest_text("Name the system", 60)
        assert tutor_client.requests == []
        assert response.learner_snapshot.completed_quests == ("prove-shell-alive", "name-system")
        assert _latest_attempt_record(database_connection)[:2] == ("passed", None)


def test_failed_answer_check_is_recorded_and_can_succeed_on_retry(
    migrated_database_path: Path,
) -> None:
    """A failed answer is durable without blocking a later passing answer."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _complete_current_session_objectives(database_connection)
        _complete_first_quest(database_connection)
        handle_chat_request(
            _chat_request("now"),
            _chat_dependencies(database_connection, timestamp="2026-07-19T09:00:00Z"),
        )

        assert handle_chat_request(
            _chat_request("answer Ubuntu"),
            _chat_dependencies(database_connection, timestamp="2026-07-19T09:01:00Z"),
        ).text.startswith("Not yet.\n\nQuest: Name the system")
        failed_attempt_record = _latest_attempt_record(database_connection)
        assert failed_attempt_record[:2] == ("failed", "missing-concept")
        failed_evidence = load_json(failed_attempt_record[2])
        assert failed_evidence["passed"] is False
        assert failed_evidence["validation_type"] == "interactive_question"
        assert (
            get_quest_completion(
                database_connection,
                "alice",
                CATALOG.course.id,
                "name-system",
            )
            is None
        )
        assert total_score_for_course(database_connection, "alice", CATALOG.course.id) == 30

        assert handle_chat_request(
            _chat_request("answer Debian GNU/Linux 13"),
            _chat_dependencies(database_connection, timestamp="2026-07-19T09:02:00Z"),
        ).text.startswith("Done.\n\nCompleted quest: Name the system")
        assert database_connection.execute(
            """
            select outcome, failure_reason
            from quest_attempts
            where quest_id = 'name-system'
            order by id
            """,
        ).fetchall() == [("failed", "missing-concept"), ("passed", None)]
        assert (
            get_quest_completion(
                database_connection,
                "alice",
                CATALOG.course.id,
                "name-system",
            )
            is not None
        )
        assert total_score_for_course(database_connection, "alice", CATALOG.course.id) == 60


def test_cli_questions_reach_tutor_during_interactive_quest(
    migrated_database_path: Path,
) -> None:
    """Questions remain tutoring requests instead of failed quest answers."""
    tutor_client = _RecordingTutorClient("guide answers Linux questions.")
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _complete_current_session_objectives(database_connection)
        _write_completed_quests(database_connection, ("prove-shell-alive", "name-system"))

        for message in (
            'explain the "ls -la ~" command',
            "what is the find command",
            "how does tmux work",
        ):
            response = handle_chat_request(
                ChatRequest(
                    context=CliChatContext(username="alice", terminal="/dev/pts/1"),
                    visibility="private",
                    text=message,
                ),
                _chat_dependencies(database_connection, tutor_client=tutor_client),
            )

            assert response.text == "guide answers Linux questions."
        assert [request.message for request in tutor_client.requests] == [
            'explain the "ls -la ~" command',
            "what is the find command",
            "how does tmux work",
        ]
        assert _attempt_count(database_connection) == 0


def test_cli_bare_count_completes_home_entries_quest(
    migrated_database_path: Path,
) -> None:
    """The terse CLI answer from the classroom transcript completes the count quest."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _complete_current_session_objectives(database_connection)
        _write_completed_quests(database_connection, ("prove-shell-alive", "name-system"))

        response = handle_chat_request(
            ChatRequest(
                context=CliChatContext(username="alice", terminal="/dev/pts/1"),
                visibility="private",
                text="6",
            ),
            _chat_dependencies(database_connection),
        )

        assert response.text == _completed_quest_text("Count your home entries", 30)
        assert response.learner_snapshot.completed_quests == (
            "prove-shell-alive",
            "name-system",
            "count-home-entries",
        )
        assert _latest_attempt_record(database_connection)[:2] == ("passed", None)


def test_check_intent_completes_file_only_quest_from_filesystem(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Chat check can complete a catalog file-content quest from filesystem evidence."""
    learner_home = tmp_path / "alice"
    playground_path = learner_home / "playground"
    playground_path.mkdir(parents=True)
    (playground_path / "micro-note.txt").write_text("edited with micro\n", encoding="utf-8")

    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, session_reached="S2")
        _complete_current_session_objectives(database_connection, "S2")
        _write_completed_quests(
            database_connection,
            (
                "prove-shell-alive",
                "name-system",
                "count-home-entries",
                "explain-ls",
                "read-file-ends",
                "build-playground",
            ),
        )

        response = handle_chat_request(
            _chat_request("check my work"),
            _chat_dependencies(database_connection, account_lookup=_account_lookup(learner_home)),
        )

        assert response.text == _completed_quest_text("Edit with micro", 30)
        assert _latest_attempt_record(database_connection)[:2] == ("passed", None)
        assert load_json(_latest_attempt_record(database_connection)[2]) == {
            "byte_count": 18,
            "catalog_path": "~/playground/micro-note.txt",
            "failure_reason": None,
            "forbidden_matched": None,
            "passed": True,
            "path_category": "learner-home",
            "required_matched": True,
            "validation_type": "file_check",
        }
        assert (
            get_quest_completion(
                database_connection,
                "alice",
                CATALOG.course.id,
                "edit-with-micro",
            )
            is not None
        )


def test_guide_check_completes_ownership_proof(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Guide check completes the ownership quest from matching owned file evidence."""
    learner_home = tmp_path / "alice"
    playground_path = learner_home / "playground"
    playground_path.mkdir(parents=True)
    hostname_path = playground_path / "hostname"
    hostname_path.write_bytes(Path("/etc/hostname").read_bytes())

    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, session_reached="S2")
        _complete_current_session_objectives(database_connection, "S2")
        _write_completed_quests(
            database_connection,
            _completed_quest_ids_before("copy-and-inspect-ownership"),
        )
        handle_chat_request(
            _chat_request("today"),
            _chat_dependencies(
                database_connection,
                account_lookup=_account_lookup(learner_home, hostname_path.stat().st_uid),
                timestamp="2026-07-19T09:00:00Z",
            ),
        )
        response = handle_chat_request(
            _chat_request("check"),
            _chat_dependencies(
                database_connection,
                account_lookup=_account_lookup(learner_home, hostname_path.stat().st_uid),
                timestamp="2026-07-19T09:01:00Z",
            ),
        )

        assert response.text == _completed_quest_text("Copy and inspect ownership", 30)
        assert _latest_attempt_record(database_connection)[:2] == ("passed", None)


def test_check_intent_completes_path_exists_quest_from_filesystem(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Chat check can complete a catalog path-existence quest from filesystem evidence."""
    learner_home = tmp_path / "alice"
    playground_path = learner_home / "playground"
    playground_path.mkdir(parents=True)
    for playground_file_name in ("one.txt", "two.txt", "three.txt"):
        (playground_path / playground_file_name).write_text("ready\n", encoding="utf-8")

    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, session_reached="S2")
        _complete_current_session_objectives(database_connection, "S2")
        _write_completed_quests(
            database_connection,
            (
                "prove-shell-alive",
                "name-system",
                "count-home-entries",
                "explain-ls",
                "read-file-ends",
            ),
        )

        response = handle_chat_request(
            _chat_request("check my work"),
            _chat_dependencies(database_connection, account_lookup=_account_lookup(learner_home)),
        )

        assert response.text == _completed_quest_text("Build a playground", 30)
        attempt_record = _latest_attempt_record(database_connection)
        assert attempt_record[:2] == ("passed", None)
        assert load_json(attempt_record[2]) == {
            "existing_count": 4,
            "failure_reason": None,
            "passed": True,
            "paths": [
                {
                    "catalog_path": "~/playground",
                    "passed": True,
                    "failure_reason": None,
                },
                {
                    "catalog_path": "~/playground/one.txt",
                    "passed": True,
                    "failure_reason": None,
                },
                {
                    "catalog_path": "~/playground/two.txt",
                    "passed": True,
                    "failure_reason": None,
                },
                {
                    "catalog_path": "~/playground/three.txt",
                    "passed": True,
                    "failure_reason": None,
                },
            ],
            "required_count": 4,
            "validation_type": "path_exists",
        }
        assert (
            get_quest_completion(
                database_connection,
                "alice",
                CATALOG.course.id,
                "build-playground",
            )
            is not None
        )


def test_check_intent_completes_executable_file_quest(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Chat check can complete a catalog quest requiring script content and mode bits."""
    learner_home = tmp_path / "alice"
    playground_path = learner_home / "playground"
    playground_path.mkdir(parents=True)
    script_path = playground_path / "run-me.sh"
    script_path.write_text("#!/bin/bash\necho ready\n", encoding="utf-8")
    script_path.chmod(0o700)

    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, session_reached="S4")
        _complete_current_session_objectives(database_connection, "S4")
        _write_completed_quests(
            database_connection,
            _completed_quest_ids_before("make-file-executable"),
        )

        response = handle_chat_request(
            _chat_request("check my work"),
            _chat_dependencies(
                database_connection,
                account_lookup=_account_lookup(learner_home, script_path.stat().st_uid),
            ),
        )

        assert response.text == _completed_quest_text("Make a file executable", 30)
        attempt_record = _latest_attempt_record(database_connection)
        assert attempt_record[:2] == ("passed", None)
        evidence = load_json(attempt_record[2])
        checks = cast("list[dict[str, object]]", evidence["checks"])
        assert evidence["validation_type"] == "all_of"
        assert checks[0]["validation_type"] == "file_check"
        assert checks[0]["catalog_path"] == "~/playground/run-me.sh"
        assert checks[0]["required_matched"] is True
        assert checks[1] == {
            "executable_count": 1,
            "failure_reason": None,
            "passed": True,
            "paths": [
                {
                    "catalog_path": "~/playground/run-me.sh",
                    "passed": True,
                    "failure_reason": None,
                },
            ],
            "required_count": 1,
            "validation_type": "executable_path",
        }
        assert (
            get_quest_completion(
                database_connection,
                "alice",
                CATALOG.course.id,
                "make-file-executable",
            )
            is not None
        )


def test_check_intent_completes_user_port_file_quest(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Chat check can complete the site.service quest from file and command evidence."""
    learner_home = tmp_path / "alice"
    service_directory = learner_home / ".config" / "systemd" / "user"
    service_directory.mkdir(parents=True)
    (service_directory / "site.service").write_text(
        """[Unit]
Description=Alice site
[Service]
WorkingDirectory=%h/public_html
ExecStart=/usr/bin/python3 -m http.server 14242 --bind 127.0.0.1
[Install]
WantedBy=default.target
""",
        encoding="utf-8",
    )

    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, session_reached="S8")
        _complete_current_session_objectives(database_connection, "S8")
        _write_completed_quests(
            database_connection,
            tuple(
                quest.id
                for quest in CATALOG.course.quests
                if quest.sequence < CATALOG.quest("enable-site-service").sequence
            ),
        )
        handle_chat_request(
            _chat_request("today"),
            _chat_dependencies(
                database_connection,
                account_lookup=_account_lookup(learner_home),
                timestamp="2026-07-19T09:00:00Z",
            ),
        )
        systemctl_observation_id = add_command_observation(
            database_connection,
            _command_observation(
                "systemctl --user enable --now site.service",
                observed_at="2026-07-19T09:01:00Z",
            ),
        )
        curl_observation_id = add_command_observation(
            database_connection,
            _command_observation(
                "curl -I http://127.0.0.1:14242/",
                observed_at="2026-07-19T09:01:00Z",
            ),
        )
        response = handle_chat_request(
            _chat_request("check my work"),
            _chat_dependencies(
                database_connection,
                account_lookup=_account_lookup(learner_home),
                timestamp="2026-07-19T09:02:00Z",
            ),
        )

        assert response.text == _completed_quest_text("Enable site.service", 30)
        attempt_record = _latest_attempt_record(database_connection)
        assert attempt_record[:2] == ("passed", None)
        evidence = load_json(attempt_record[2])
        checks = cast("list[dict[str, object]]", evidence["checks"])
        assert evidence["validation_type"] == "all_of"
        assert checks[0]["validation_type"] == "user_port_file"
        assert checks[0]["computed_port"] == 14242
        assert checks[0]["required_matched"] is True
        assert checks[1] == {
            "failure_reason": None,
            "matched_count": 2,
            "matched_commands": ["systemctl --user", "curl"],
            "matched_observation_ids": [systemctl_observation_id, curl_observation_id],
            "missing_commands": [],
            "observed_count": 2,
            "observed_since": "2026-07-19T09:00:00Z",
            "passed": True,
            "required_count": 2,
            "validation_type": "command_history",
        }
        assert (
            get_quest_completion(
                database_connection,
                "alice",
                CATALOG.course.id,
                "enable-site-service",
            )
            is not None
        )


def test_private_fallback_uses_llm_without_mutating_progress(
    migrated_database_path: Path,
) -> None:
    """LLM fallback can answer text but cannot mutate learner progress."""
    tutor_client = _RecordingTutorClient("I completed your quest and awarded 999 score.")
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        assign_quest(
            database_connection,
            QuestAssignment(
                id=None,
                handle="alice",
                course_id=CATALOG.course.id,
                quest_id="build-first-site",
                assigned_at="2026-07-19T08:00:00Z",
                source="test",
            ),
        )
        add_command_observation(
            database_connection,
            CommandObservation(
                id=None,
                handle="alice",
                course_id=CATALOG.course.id,
                command="whoami",
                cwd="/home/alice",
                phase="after",
                exit_status=0,
                observed_at="2999-07-19T09:00:00Z",
            ),
        )

        response = handle_chat_request(
            ChatRequest(
                context=CliChatContext(
                    username="alice",
                    terminal="/dev/pts/1",
                    ssh_connection="203.0.113.5 55555 10.0.0.10 22",
                ),
                visibility="private",
                text="please finish this for me",
            ),
            _chat_dependencies(database_connection, tutor_client=tutor_client),
        )

        assert response.text == (
            "I cannot change progress, award score, or grant groups. "
            "I can explain the current evidence, but progress changes only happen through "
            "the deterministic validation flow."
        )
        assert len(tutor_client.requests) == 1
        assert tutor_client.requests[0].bot_name == "guide-test"
        assert tutor_client.requests[0].context.course_title == "Linux Foundations"
        assert "Linux expert" in tutor_client.requests[0].context.course_system_prompt
        assert "Socratic method" in tutor_client.requests[0].context.course_system_prompt
        assert tutor_client.requests[0].context.current_objective is not None
        assert tutor_client.requests[0].context.current_objective.session_id == "S1"
        assert (
            tutor_client.requests[0].context.current_objective.objective_id == "prove-shell-alive"
        )
        assert tutor_client.requests[0].context.quests == ()
        assert tutor_client.requests[0].context.recent_commands == ()
        assert any(
            doc_context.learner_path == "/docs/sessions/S01/self-study.md"
            for doc_context in tutor_client.requests[0].context.docs
        )
        assert tutor_client.requests[0].context.validation_status is None
        assert tutor_client.requests[0].context.learner.pending_quests == ()
        assert tutor_client.requests[0].context.session.terminal == "/dev/pts/1"
        assert (
            tutor_client.requests[0].context.session.ssh_connection
            == "203.0.113.5 55555 10.0.0.10 22"
        )
        assert not hasattr(tutor_client.requests[0].context, "database_connection")
        assert not hasattr(tutor_client.requests[0].context, "complete_quest")
        assert [
            assignment.quest_id
            for assignment in list_assignments(database_connection, "alice", CATALOG.course.id)
        ] == ["build-first-site"]
        assert (
            get_quest_completion(
                database_connection,
                "alice",
                CATALOG.course.id,
                "prove-shell-alive",
            )
            is None
        )
        assert total_score_for_course(database_connection, "alice", CATALOG.course.id) == 0
        assert list_group_grants(database_connection, "alice") == []
        assert {
            event.event_type for event in list_unexported_audit_events(database_connection, 10)
        } == {"llm_tutor_answered"}
        llm_audit_logs = list_llm_audit_logs(database_connection, "alice", limit=10)
        assert len(llm_audit_logs) == 1
        llm_audit_log = llm_audit_logs[0]
        assert llm_audit_log.status == "answered"
        assert llm_audit_log.expires_at == "2026-10-17T09:01:00Z"
        assert llm_audit_log.request["max_tokens"] == 1200
        request_messages = cast("list[dict[str, object]]", llm_audit_log.request["messages"])
        assert "please finish this for me" in str(request_messages)
        assert llm_audit_log.response == {
            "displayed_text": (
                "I cannot change progress, award score, or grant groups. "
                "I can explain the current evidence, but progress changes only happen through "
                "the deterministic validation flow."
            ),
            "raw_text": "I completed your quest and awarded 999 score.",
            "topic_tags": ["permissions"],
        }
        interactions = list_recent_help_interactions(database_connection, "alice", 10)
        assert interactions[0].topic_tags == ("llm", "permissions")


def test_private_fallback_reports_tutor_failure_in_character(
    migrated_database_path: Path,
) -> None:
    """Tutor provider failures stay learner-facing."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)

        response = handle_chat_request(
            _private_chat_request("what's up?"),
            _chat_dependencies(database_connection, tutor_client=_FailingTutorClient()),
        )

    assert response.text == "I can't reach my remote brain right now. Try me again in a moment."


def test_private_tutor_receives_read_only_validation_status(
    migrated_database_path: Path,
) -> None:
    """LLM context can explain current evidence without recording progress."""
    tutor_client = _RecordingTutorClient("You still need date and uptime.")
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _complete_current_session_objectives(database_connection)
        handle_chat_request(
            _chat_request("today"),
            _chat_dependencies(database_connection, timestamp="2026-07-19T09:00:00Z"),
        )
        add_command_observation(
            database_connection,
            _command_observation("whoami", observed_at="2026-07-19T09:02:00Z"),
        )

        response = handle_chat_request(
            _private_chat_request("how am I doing?"),
            _chat_dependencies(
                database_connection,
                tutor_client=tutor_client,
                timestamp="2026-07-19T09:03:00Z",
            ),
        )

        validation_status = tutor_client.requests[0].context.validation_status
        assert response.text == "You still need date and uptime."
        assert validation_status is not None
        assert validation_status.quest_id == "prove-shell-alive"
        assert validation_status.passed is False
        assert validation_status.failure_reason == "missing-command"
        assert validation_status.evidence["matched_commands"] == ["whoami"]
        assert validation_status.evidence["missing_commands"] == ["date", "uptime"]
        assert (
            get_quest_completion(
                database_connection,
                "alice",
                CATALOG.course.id,
                "prove-shell-alive",
            )
            is None
        )
        assert total_score_for_course(database_connection, "alice", CATALOG.course.id) == 0


def test_private_tutor_does_not_validate_stale_earlier_session_assignment(
    migrated_database_path: Path,
) -> None:
    """Tutor validation follows the current-session-first pending quest order."""
    tutor_client = _RecordingTutorClient("Start Count a stream.")
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, session_reached="S3")
        _complete_current_session_objectives(database_connection, "S3")
        assign_quest(
            database_connection,
            QuestAssignment(
                id=None,
                handle="alice",
                course_id=CATALOG.course.id,
                quest_id="name-system",
                assigned_at="2026-07-19T09:00:00Z",
                source="chat",
            ),
        )

        handle_chat_request(
            _private_chat_request("what should I do now?"),
            _chat_dependencies(database_connection, tutor_client=tutor_client),
        )

    assert tutor_client.requests[0].context.learner.pending_quests[0] == "count-stream"
    assert [
        (quest.quest_id, quest.available_after_session)
        for quest in tutor_client.requests[0].context.quests
    ] == [("count-stream", "S3")]
    assert tutor_client.requests[0].context.validation_status is None


def test_private_tutor_does_not_validate_quest_blocked_by_session_objective(
    migrated_database_path: Path,
) -> None:
    """Incomplete session objectives remain authoritative over assigned quests."""
    tutor_client = _RecordingTutorClient("Run guide now.")
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, joined_irc=False)
        assign_quest(
            database_connection,
            QuestAssignment(
                id=None,
                handle="alice",
                course_id=CATALOG.course.id,
                quest_id="prove-shell-alive",
                assigned_at="2026-07-19T09:00:00Z",
                source="chat",
            ),
        )

        handle_chat_request(
            _private_chat_request("how am I doing?"),
            _chat_dependencies(database_connection, tutor_client=tutor_client),
        )

    assert tutor_client.requests[0].context.validation_status is None


def test_private_tutor_receives_recent_private_interactions_from_its_transport(
    migrated_database_path: Path,
) -> None:
    """Tutor history is bounded, chronological, private, and transport-specific."""
    tutor_client = _RecordingTutorClient("Continue with `now`.")
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        for index in range(5):
            add_help_interaction(
                database_connection,
                _help_interaction(
                    source="irc",
                    visibility="private",
                    question="x" * 1_201 if index == 4 else f"private {index}",
                    response="y" * 1_201 if index == 4 else f"answer {index}",
                    created_at=f"2026-07-19T09:0{index}:00Z",
                ),
            )
        add_help_interaction(
            database_connection,
            _help_interaction(
                source="cli",
                visibility="private",
                question="other transport",
                response="exclude transport",
                created_at="2026-07-19T09:06:00Z",
            ),
        )
        add_help_interaction(
            database_connection,
            _help_interaction(
                source="irc",
                visibility="public",
                question="public interaction",
                response="exclude visibility",
                created_at="2026-07-19T09:07:00Z",
            ),
        )

        handle_chat_request(
            _private_chat_request("what next?"),
            _chat_dependencies(database_connection, tutor_client=tutor_client),
        )

    recent_interactions = tutor_client.requests[0].context.recent_interactions
    assert [interaction.question for interaction in recent_interactions[:3]] == [
        "private 1",
        "private 2",
        "private 3",
    ]
    assert recent_interactions[3].question == f"{'x' * 1_197}..."
    assert [interaction.response for interaction in recent_interactions[:3]] == [
        "answer 1",
        "answer 2",
        "answer 3",
    ]
    assert recent_interactions[3].response == f"{'y' * 1_197}..."


def test_private_tutor_audit_rolls_back_when_help_logging_fails(
    migrated_database_path: Path,
) -> None:
    """Private tutor provider calls stay external while local audit writes are atomic."""
    tutor_client = _RecordingTutorClient("Use `guide now` first.")
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        _block_help_interaction_inserts(database_connection)

        with pytest.raises(sqlite3.IntegrityError, match="help interaction insert blocked"):
            handle_chat_request(
                _private_chat_request("what should I do?"),
                _chat_dependencies(database_connection, tutor_client=tutor_client),
            )

        assert len(tutor_client.requests) == 1
        assert list_llm_audit_logs(database_connection, "alice", limit=10) == []
        assert list_unexported_audit_events(database_connection, 10) == []
        assert "what should I do?" not in _help_interaction_questions(database_connection)


def test_llm_audit_logs_are_not_replayed_into_future_tutor_context(
    migrated_database_path: Path,
) -> None:
    """Restricted LLM audit content is not part of future read-only tutor context."""
    tutor_client = _RecordingTutorClient("safe answer")
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)
        append_llm_audit_log(database_connection, _llm_audit_log())

        handle_chat_request(
            _private_chat_request("what now?"),
            _chat_dependencies(database_connection, tutor_client=tutor_client),
        )

        assert len(tutor_client.requests) == 1
        assert "prior private prompt" not in str(tutor_client.requests[0].context)
        assert "prior raw response" not in str(tutor_client.requests[0].context)


def test_public_fallback_does_not_call_llm_or_expose_private_state(
    migrated_database_path: Path,
) -> None:
    """Public LLM fallback refuses private learner-state tutoring."""
    tutor_client = _RecordingTutorClient("private state")
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)

        response = handle_chat_request(
            _chat_request("why am I stuck?"),
            _chat_dependencies(database_connection, tutor_client=tutor_client),
        )

        assert response.text == (
            "Ask me privately for tutoring so I do not expose your learner state in public."
        )
        assert tutor_client.requests == []
        assert list_assignments(database_connection, "alice", CATALOG.course.id) == []
        assert total_score_for_course(database_connection, "alice", CATALOG.course.id) == 0
        assert list_group_grants(database_connection, "alice") == []


@pytest.mark.parametrize(
    ("message", "expected_prefix"),
    [
        ("today", "Current session objective: Confirm that your shell is working"),
        ("check my work", "Current session objective: Confirm that your shell is working"),
    ],
)
def test_deterministic_intents_bypass_llm(
    migrated_database_path: Path,
    message: str,
    expected_prefix: str,
) -> None:
    """Deterministic chat intents do not call the LLM provider."""
    tutor_client = _RecordingTutorClient("should not be used")
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection)

        response = handle_chat_request(
            _chat_request(message),
            _chat_dependencies(database_connection, tutor_client=tutor_client),
        )

        assert response.text.startswith(expected_prefix)
    assert tutor_client.requests == []


def test_irc_check_marks_missing_client_evidence_as_retryable(
    migrated_database_path: Path,
) -> None:
    """IRC check can ask for client evidence and retry without showing a failed check."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, session_reached="S9")
        _complete_current_session_objectives(database_connection, "S9")
        _write_completed_quests(
            database_connection,
            _completed_quest_ids_before("use-terminal-irc"),
        )
        assign_quest(
            database_connection,
            QuestAssignment(
                id=None,
                handle="alice",
                course_id=CATALOG.course.id,
                quest_id="use-terminal-irc",
                assigned_at="2026-10-24T09:00:00Z",
                source="test",
            ),
        )

        response = handle_chat_request(
            _chat_request("check"),
            _chat_dependencies(database_connection, timestamp="2026-10-24T09:01:00Z"),
        )

    assert response.retry_after_irc_client_verification is True
    assert "Not yet." in response.text


def _write_member(
    database_connection: sqlite3.Connection,
    session_reached: str = "S1",
    *,
    joined_irc: bool = True,
    released_at: str | None = None,
) -> None:
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
            session_reached=session_reached,
            released_at=(
                released_at
                or CATALOG.session(session_reached).starts_at.isoformat().replace("+00:00", "Z")
            ),
        ),
    )
    if joined_irc and session_reached == "S1":
        complete_session_objective(
            database_connection,
            SessionObjectiveCompletion(
                handle="alice",
                course_id=CATALOG.course.id,
                session_id="S1",
                objective_id="join-course-irc",
                completed_at="2026-07-18T09:00:00Z",
                evidence_json="{}",
            ),
        )


def _chat_request(text: str) -> ChatRequest:
    return ChatRequest(
        context=IrcChatContext(
            nickname="alice",
            target="#kolam",
            reply_target="#kolam",
        ),
        visibility="public",
        text=text,
    )


def _complete_current_session_objectives(
    database_connection: sqlite3.Connection,
    session_id: str = "S1",
) -> None:
    with database_connection:
        for session in CATALOG.sessions_through(session_id):
            for objective in session.objectives:
                complete_session_objective(
                    database_connection,
                    SessionObjectiveCompletion(
                        handle="alice",
                        course_id=CATALOG.course.id,
                        session_id=session.id,
                        objective_id=objective.id,
                        completed_at="2026-07-19T08:00:00Z",
                        evidence_json="{}",
                    ),
                )


def _chat_dependencies(
    database_connection: sqlite3.Connection,
    tutor_client: TutorClient | None = None,
    answer_interpreter: AnswerInterpreter | None = None,
    account_lookup: UnixAccountLookup = lookup_unix_account,
    timestamp: str = "2026-07-19T09:01:00Z",
) -> ChatDependencies:
    return ChatDependencies(
        database_connection=database_connection,
        catalog=CATALOG,
        bot_name="guide-test",
        tutor_client=tutor_client,
        answer_interpreter=answer_interpreter,
        timestamp_factory=lambda: timestamp,
        account_lookup=account_lookup,
    )


def _complete_first_quest(database_connection: sqlite3.Connection) -> None:
    handle_chat_request(
        _chat_request("today"),
        _chat_dependencies(database_connection, timestamp="2026-07-19T08:00:00Z"),
    )
    for command in ("whoami", "date", "uptime"):
        add_command_observation(
            database_connection,
            _command_observation(command, observed_at="2026-07-19T08:01:00Z"),
        )
    handle_chat_request(
        _chat_request("check my work"),
        _chat_dependencies(database_connection, timestamp="2026-07-19T08:02:00Z"),
    )


def _write_completed_quests(
    database_connection: sqlite3.Connection,
    quest_ids: tuple[str, ...],
) -> None:
    with database_connection:
        for quest_id in quest_ids:
            write_quest_completion(
                database_connection,
                QuestCompletion(
                    handle="alice",
                    course_id=CATALOG.course.id,
                    quest_id=quest_id,
                    attempt_id=None,
                    completed_at="2026-07-19T09:00:00Z",
                    source="test",
                ),
            )


def _completed_quest_ids_before(quest_id: str) -> tuple[str, ...]:
    return tuple(
        quest.id
        for quest in CATALOG.course.quests
        if quest.sequence < CATALOG.quest(quest_id).sequence
    )


def _completed_quest_text(quest_title: str, score: int) -> str:
    return (
        f"Done.\n\nCompleted quest: {quest_title}\n\nScore: {score}\n\n"
        "Tier: newcomer\n\nNext: guide now"
    )


def _llm_audit_log() -> LlmAuditLog:
    return LlmAuditLog(
        id=None,
        handle="alice",
        course_id=CATALOG.course.id,
        source="test",
        created_at="2026-07-19T08:00:00Z",
        provider="openrouter",
        model="deepseek/deepseek-v4-flash",
        status="answered",
        request={"messages": [{"role": "user", "content": "prior private prompt"}]},
        response={"raw_text": "prior raw response", "displayed_text": "prior safe response"},
        expires_at="2026-10-17T08:00:00Z",
    )


def _help_interaction(
    source: str,
    visibility: str,
    question: str,
    response: str,
    created_at: str,
) -> HelpInteraction:
    return HelpInteraction(
        id=None,
        handle="alice",
        source=source,
        visibility=visibility,
        question=question,
        response=response,
        topic_tags=(),
        created_at=created_at,
        answered_at=created_at,
    )


def _private_chat_request(text: str) -> ChatRequest:
    return ChatRequest(
        context=IrcChatContext(
            nickname="alice",
            target="maker-guide",
            reply_target="alice",
        ),
        visibility="private",
        text=text,
    )


class _RecordingTutorClient:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.requests: list[TutorRequest] = []

    def answer(
        self,
        tutor_request: TutorRequest,
        chunk_writer: Callable[[str], None] | None = None,
    ) -> TutorResponse:
        del chunk_writer
        self.requests.append(tutor_request)
        return TutorResponse(
            text=self.response_text,
            topic_tags=("permissions",),
            model="deepseek/deepseek-v4-flash",
            provider="test",
        )


class _FailingTutorClient:
    def answer(
        self,
        tutor_request: TutorRequest,
        chunk_writer: Callable[[str], None] | None = None,
    ) -> TutorResponse:
        del tutor_request, chunk_writer
        raise TutorError("provider unavailable")


class _RecordingAnswerInterpreter:
    def __init__(
        self,
        database_connection: sqlite3.Connection,
        components: tuple[AnswerComponentAnalysis, ...],
        feedback: str | None = None,
        on_interpret: Callable[[], None] | None = None,
    ) -> None:
        self._database_connection = database_connection
        self._components = components
        self._feedback = feedback
        self._on_interpret = on_interpret
        self.requests: list[AnswerInterpretationRequest] = []

    def interpret_answer(self, request: AnswerInterpretationRequest) -> AnswerInterpretation:
        assert self._database_connection.in_transaction is False
        self.requests.append(request)
        if self._on_interpret is not None:
            self._on_interpret()
        return AnswerInterpretation(
            components=self._components,
            feedback=self._feedback,
            provider="test",
            model="test-model",
            raw_arguments="{}",
        )


def _component(
    concept_id: str,
    verdict: str,
    evidence_quote: str | None,
) -> AnswerComponentAnalysis:
    return AnswerComponentAnalysis(
        concept_id=concept_id,
        verdict=cast("AnswerVerdict", verdict),
        evidence_quote=evidence_quote,
    )


def _prepare_combine_streams_objective(
    database_connection: sqlite3.Connection,
    learner_home: Path,
) -> None:
    (learner_home / "playground").mkdir(parents=True)
    (learner_home / "playground" / "combined.txt").write_text(
        "date: output format: %F\n2026-08-01\n",
        encoding="utf-8",
    )
    _write_member(database_connection, session_reached="S3")
    _complete_current_session_objectives(database_connection, "S2")
    with database_connection:
        for objective in CATALOG.session("S3").objectives:
            if objective.id == "combine-and-copy-streams":
                break
            complete_session_objective(
                database_connection,
                SessionObjectiveCompletion(
                    handle="alice",
                    course_id=CATALOG.course.id,
                    session_id="S3",
                    objective_id=objective.id,
                    completed_at="2026-08-01T09:00:00Z",
                    evidence_json="{}",
                ),
            )
    add_command_observation(
        database_connection,
        _command_observation(
            "date --debug +%F 2>&1 | tee ~/playground/combined.txt | wc -l",
            observed_at="2026-08-01T09:01:00Z",
        ),
    )
    database_connection.commit()


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


def _account_lookup(learner_home: Path, user_id: int = 4242) -> UnixAccountLookup:
    def lookup(handle: str) -> UnixAccount | None:
        if handle != "alice":
            return None
        return UnixAccount(handle=handle, user_id=user_id, home_directory=learner_home)

    return lookup


def _latest_attempt_record(database_connection: sqlite3.Connection) -> tuple[str, str | None, str]:
    attempt_record = cast(
        "tuple[str, str | None, str] | None",
        database_connection.execute(
            """
            select outcome, failure_reason, evidence_json
            from quest_attempts
            order by id desc
            limit 1
            """,
        ).fetchone(),
    )
    if attempt_record is None:
        raise AssertionError("expected a quest attempt")
    return attempt_record


def _attempt_count(database_connection: sqlite3.Connection) -> int:
    return cast(
        "tuple[int]",
        database_connection.execute("select count(*) from quest_attempts").fetchone(),
    )[0]


def _help_interaction_questions(database_connection: sqlite3.Connection) -> frozenset[str]:
    return frozenset(
        interaction.question
        for interaction in list_recent_help_interactions(database_connection, "alice", 20)
    )


def _block_help_interaction_inserts(database_connection: sqlite3.Connection) -> None:
    database_connection.execute(
        """
        create temp trigger block_help_interaction_inserts
        before insert on help_interactions
        begin
            select raise(abort, 'help interaction insert blocked');
        end
        """,
    )


def _write_conflicting_score(database_connection: sqlite3.Connection, quest_id: str) -> None:
    add_score_entry(
        database_connection,
        ScoreLedgerEntry(
            id=None,
            handle="alice",
            course_id=CATALOG.course.id,
            amount=1,
            reason="quest_completed",
            related_type="quest",
            related_id=quest_id,
            created_at="2026-07-19T08:59:00Z",
        ),
    )
