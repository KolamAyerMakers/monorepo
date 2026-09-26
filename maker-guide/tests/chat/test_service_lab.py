"""Chat-level service challenges use durable runs and fresh, task-bound evidence."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from maker_guide.chat.contract import (
    ChatDependencies,
    ChatRequest,
    ChatResponse,
    CliChatContext,
    IrcChatContext,
)
from maker_guide.chat.service import handle_chat_request
from maker_guide.chat.service_lab import prepare_service_lab
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.curriculum.models import ServiceLabValidation
from maker_guide.llm_tutor import (
    AnswerComponentAnalysis,
    AnswerInterpretation,
    AnswerInterpretationRequest,
    TutorError,
    TutorRequest,
    TutorResponse,
)
from maker_guide.progress.service import current_session_objective
from maker_guide.repositories.cohort_membership import CohortMembership, upsert_membership
from maker_guide.repositories.course_release import CourseRelease, upsert_course_release
from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.learner import Learner, upsert_learner
from maker_guide.repositories.score_ledger import list_score_entries, total_score_for_course
from maker_guide.repositories.service_lab_attempt import get_attempt
from maker_guide.repositories.session_objective_completion import (
    SessionObjectiveCompletion,
    complete_session_objective,
    list_completed_objective_ids,
)
from maker_guide.service_lab import ServiceLabAction, ServiceLabReport

_TIMESTAMP = "2026-09-26T10:00:00Z"
_NEGATED_ANSWER = (
    "It is false that ExecStart path was missing, and false that I restored "
    "ExecStart path to /usr/bin/caddy, reloaded and restarted."
)
_SEMANTIC_ANSWER = (
    "It could not find the program, so I pointed it at the real Caddy binary "
    "and had systemd reread the unit and launch it again."
)


def test_service_lab_repair_and_explanation_advance_through_five_durable_challenges(  # noqa: PLR0915 - one learner lifecycle
    migrated_database_path: Path,
) -> None:
    """With no prior exercise credit, all five repairs advance once and survive reconnects."""
    actions: list[ServiceLabAction] = []
    interpretations: list[AnswerInterpretationRequest] = []
    healthy = False
    with closing(connect_database(migrated_database_path)) as database_connection:
        completed = _seed_s8_prerequisites(database_connection)
        assert not completed

    def run_service_lab(
        action: ServiceLabAction, database_connection: sqlite3.Connection
    ) -> ServiceLabReport:
        assert not database_connection.in_transaction
        with closing(connect_database(migrated_database_path)) as observer:
            current = current_session_objective(observer, CATALOG, handle="alice")
            assert current.objective is not None
            attempt = get_attempt(observer, "alice", CATALOG.course.id, "S8", current.objective.id)
            assert attempt is not None
            assert (attempt.run_id, attempt.scenario) == (action.run_id, action.scenario)
            assert (attempt.started_at is None) is (action.operation == "start")
        actions.append(action)
        return _report(action, healthy=healthy)

    def send(message: str) -> ChatResponse:
        with closing(connect_database(migrated_database_path)) as database_connection:
            interpreter = _RecordingAnswerInterpreter(database_connection)
            response = handle_chat_request(
                _request(message),
                replace(
                    _dependencies(
                        database_connection,
                        lambda action: run_service_lab(action, database_connection),
                    ),
                    answer_interpreter=interpreter,
                ),
            )
            assert not database_connection.in_transaction
            interpretations.extend(interpreter.requests)
            return response

    challenges = (
        ("break-and-read-error", "missing-executable", _SEMANTIC_ANSWER),
        (
            "repair-service-arguments",
            "invalid-argument",
            "Caddy rejected the bad flag, so I fixed it, reloaded and restarted.",
        ),
        (
            "repair-service-content",
            "empty-root",
            "It served an empty folder, so I fixed the root, reloaded and restarted.",
        ),
        (
            "repair-service-response",
            "wrong-content",
            "HTTP 200 served the wrong page, so I fixed the root, reloaded and restarted.",
        ),
        (
            "rebuild-published-site",
            "missing-published-site",
            "The output folder was gone, so I rebuilt it from source without restarting Caddy.",
        ),
    )
    for index, (objective_id, scenario, answer) in enumerate(challenges):
        healthy = False
        count = len(actions)
        send(f"answer {answer}")
        assert len(actions) == count
        launch = send("now")
        assert actions[-1].operation == "start"
        assert actions[-1].scenario == scenario
        assert all(
            secret not in launch.text.casefold()
            for secret in (
                scenario,
                "execstart",
                "--access-logs",
                "203/exec",
                "unknown flag",
                "private unit diagnostic",
                "private journal diagnostic",
            )
        )
        for message in ("next", "now", f"answer {answer}"):
            send(message)
        healthy = True
        send("check")
        assert len(interpretations) == index
        with closing(connect_database(migrated_database_path)) as database_connection:
            assert (
                list_completed_objective_ids(database_connection, "alice", CATALOG.course.id, "S8")
                == completed
            )
            before = list_score_entries(database_connection, "alice", CATALOG.course.id)
        send(f"answer {answer}")
        assert len(interpretations) == index + 1
        assert interpretations[-1].answer == answer
        assert [action.operation for action in actions[count:]] == ["start", *(["inspect"] * 5)]
        assert len({action.run_id for action in actions[count:]}) == 1
        completed |= {objective_id}
        with closing(connect_database(migrated_database_path)) as database_connection:
            assert (
                list_completed_objective_ids(database_connection, "alice", CATALOG.course.id, "S8")
                == completed
            )
            scores = list_score_entries(database_connection, "alice", CATALOG.course.id)
            assert len(scores) > len(before)
            assert [
                entry.related_id
                for entry in scores
                if entry.reason == "session_objective_completed"
            ] == [f"S8:{challenge[0]}" for challenge in challenges[: index + 1]]
            current = current_session_objective(database_connection, CATALOG, handle="alice")
            assert current.session_id == ("S8" if index + 1 < len(challenges) else "S1")
            assert (current.objective.id if current.objective else None) == (
                challenges[index + 1][0] if index + 1 < len(challenges) else "join-course-irc"
            )
        count = len(actions)
        send(f"answer {answer}")
        with closing(connect_database(migrated_database_path)) as database_connection:
            assert list_score_entries(database_connection, "alice", CATALOG.course.id) == scores
        assert len(actions) == count
    finished_actions = tuple(actions)
    with closing(connect_database(migrated_database_path)) as database_connection:
        finished_scores = list_score_entries(database_connection, "alice", CATALOG.course.id)
    for message in ("now", "check", f"answer {_SEMANTIC_ANSWER}"):
        send(message)
    assert tuple(actions) == finished_actions
    assert len({action.run_id for action in actions}) == 5
    with closing(connect_database(migrated_database_path)) as database_connection:
        assert (
            list_score_entries(database_connection, "alice", CATALOG.course.id) == finished_scores
        )


def test_service_lab_launch_messages_rotate_without_repeating_on_inspection(
    migrated_database_path: Path,
) -> None:
    """Different launches vary their message; inspection never repeats a launch announcement."""
    with connect_database(migrated_database_path) as database_connection:
        _seed_s8_prerequisites(database_connection)
        dependencies = _dependencies(
            database_connection, lambda action: _report(action, healthy=False)
        )
        first = prepare_service_lab(_request("now"), dependencies, "alice", _TIMESTAMP)
        repeated = prepare_service_lab(_request("now"), dependencies, "alice", _TIMESTAMP)
        assert first is not None
        assert first.launch_message is not None
        assert repeated is not None
        assert repeated.launch_message is None
        _complete_objective(database_connection, "break-and-read-error")
        database_connection.commit()
        successor = prepare_service_lab(_request("now"), dependencies, "alice", _TIMESTAMP)
        assert successor is not None
        assert successor.launch_message is not None
        assert first.launch_message != successor.launch_message


@pytest.mark.parametrize(
    "grading",
    [
        "absent",
        "error",
        "partial",
        "duplicate",
        "unmatched-quote",
        "contradicted",
        "not-demonstrated",
    ],
)
def test_service_lab_negated_keyword_answer_cannot_earn_fallback_credit(
    migrated_database_path: Path,
    grading: str,
) -> None:
    """Unavailable, invalid or negative semantic assessments cannot resurrect regex credit."""
    with connect_database(migrated_database_path) as database_connection:
        prerequisites = _seed_s8_prerequisites(database_connection)
        interpreter = _RecordingAnswerInterpreter(database_connection, grading=grading)
        dependencies = replace(
            _dependencies(
                database_connection,
                lambda action: _report(action, healthy=action.operation == "inspect"),
            ),
            answer_interpreter=None if grading == "absent" else interpreter,
        )
        handle_chat_request(_request("now"), dependencies)
        handle_chat_request(_request(f"answer {_NEGATED_ANSWER}"), dependencies)
        assert len(interpreter.requests) == (0 if grading == "absent" else 1)
        assert (
            list_completed_objective_ids(database_connection, "alice", CATALOG.course.id, "S8")
            == prerequisites
        )
        assert total_score_for_course(database_connection, "alice", CATALOG.course.id) == 0


@pytest.mark.parametrize("staleness", ["wrong-run", "objective-changed", "objectives-complete"])
def test_service_lab_stale_callback_cannot_grade_or_complete_successor(
    migrated_database_path: Path,
    staleness: str,
) -> None:
    """A healthy report must still belong to the reserved run and current objective."""
    actions: list[ServiceLabAction] = []
    with connect_database(migrated_database_path) as database_connection:
        prerequisites = _seed_s8_prerequisites(database_connection)
        interpreter = _RecordingAnswerInterpreter(database_connection)

        def run_service_lab(action: ServiceLabAction) -> ServiceLabReport:
            assert not database_connection.in_transaction
            actions.append(action)
            if action.operation == "start":
                return _report(action, healthy=False)
            if staleness != "wrong-run":
                with connect_database(migrated_database_path) as concurrent_connection:
                    for objective in CATALOG.session("S8").objectives:
                        if objective.id == "break-and-read-error" or (
                            staleness == "objectives-complete"
                            and isinstance(objective.validation, ServiceLabValidation)
                        ):
                            _complete_objective(concurrent_connection, objective.id)
                return _report(action, healthy=True)
            return replace(
                _report(action, healthy=True),
                run_id="b" * 32 if action.run_id != "b" * 32 else "c" * 32,
            )

        dependencies = replace(
            _dependencies(database_connection, run_service_lab), answer_interpreter=interpreter
        )
        handle_chat_request(_request("now"), dependencies)
        response = handle_chat_request(
            _request(
                "check" if staleness == "objectives-complete" else f"answer {_SEMANTIC_ANSWER}"
            ),
            dependencies,
        )

        assert [action.operation for action in actions] == ["start", "inspect"]
        assert actions[0].run_id == actions[1].run_id
        assert interpreter.requests == []
        current = current_session_objective(database_connection, CATALOG, handle="alice")
        if staleness == "objectives-complete":
            assert current.session_id == "S1"
            assert current.objective is not None
            assert current.objective == CATALOG.session("S1").objectives[0]
            assert list_completed_objective_ids(
                database_connection, "alice", CATALOG.course.id, "S8"
            ) == {objective.id for objective in CATALOG.session("S8").objectives}
            assert current.objective.title in response.text
        else:
            assert list_completed_objective_ids(
                database_connection, "alice", CATALOG.course.id, "S8"
            ) == prerequisites | (
                {"break-and-read-error"} if staleness == "objective-changed" else set()
            )
            assert current.objective is not None
            assert current.objective.id == (
                "repair-service-arguments"
                if staleness == "objective-changed"
                else "break-and-read-error"
            )
        assert (
            get_attempt(
                database_connection, "alice", CATALOG.course.id, "S8", "repair-service-arguments"
            )
            is None
        )
        assert cast(
            "tuple[int, int, int]",
            database_connection.execute(
                """select
                (select count(*) from quest_attempts),
                (select count(*) from quest_completions),
                (select count(*) from service_lab_attempts)"""
            ).fetchone(),
        ) == (0, 0, 1)
        assert total_score_for_course(database_connection, "alice", CATALOG.course.id) == 0


@pytest.mark.parametrize(
    "message",
    ["hint", "please give me a hint", "I'm stuck with this error", "help me understand this"],
)
def test_service_lab_hint_gets_fresh_environment_without_starting_or_completing(
    migrated_database_path: Path,
    message: str,
) -> None:
    """Bare hints route to the tutor, with fresh diagnostics rather than answer grading."""
    actions: list[ServiceLabAction] = []
    reports: list[ServiceLabReport] = []
    healthy = False
    with connect_database(migrated_database_path) as database_connection:
        prerequisites = _seed_s8_prerequisites(database_connection)
        tutor = _RecordingTutorClient(database_connection)
        interpreter = _RecordingAnswerInterpreter(database_connection)

        def run_service_lab(action: ServiceLabAction) -> ServiceLabReport:
            assert not database_connection.in_transaction
            actions.append(action)
            reports.append(
                replace(
                    _report(action, healthy=healthy),
                    journal=f"private journal diagnostic from inspection {len(actions)}",
                )
            )
            return reports[-1]

        dependencies = replace(
            _dependencies(database_connection, run_service_lab),
            tutor_client=tutor,
            answer_interpreter=interpreter,
        )
        handle_chat_request(_request(message), dependencies)
        assert actions == []
        assert len(tutor.requests) == 1
        assert tutor.requests[0].context.service_lab is not None
        assert not tutor.requests[0].context.service_lab.started
        assert tutor.requests[0].context.service_lab.observation is None
        handle_chat_request(_request("now"), dependencies)
        attempt = get_attempt(
            database_connection, "alice", CATALOG.course.id, "S8", "break-and-read-error"
        )
        assert attempt is not None

        for healthy in (False, True):
            handle_chat_request(_request(message), dependencies)
            context = tutor.requests[-1].context
            assert tutor.requests[-1].message == message
            assert context.current_objective is not None
            assert context.current_objective.objective_id == "break-and-read-error"
            assert context.service_lab is not None
            assert context.service_lab.started
            assert context.service_lab.scenario == attempt.scenario
            assert context.service_lab.observation is not None
            assert context.service_lab.observation == reports[-1]
            assert context.service_lab.observation.healthy is healthy
            assert context.validation_status is not None
            assert not context.validation_status.passed
            assert context.validation_status.failure_reason == (
                "missing-answer" if healthy else "service-lab-unrepaired"
            )
            assert (
                get_attempt(
                    database_connection, "alice", CATALOG.course.id, "S8", "break-and-read-error"
                )
                == attempt
            )
            assert (
                list_completed_objective_ids(database_connection, "alice", CATALOG.course.id, "S8")
                == prerequisites
            )
        assert len(tutor.requests) == 3
        assert interpreter.requests == []
        assert [action.operation for action in actions] == ["start", "inspect", "inspect"]
        assert {action.run_id for action in actions} == {attempt.run_id}
        assert total_score_for_course(database_connection, "alice", CATALOG.course.id) == 0


def test_service_lab_bare_answer_requires_fresh_healthy_inspection(
    migrated_database_path: Path,
) -> None:
    """Unrepaired statements get tutoring; a fresh recovery enables bare causal answers."""
    healthy = False
    with connect_database(migrated_database_path) as database_connection:
        prerequisites = _seed_s8_prerequisites(database_connection)
        tutor = _RecordingTutorClient(database_connection)
        interpreter = _RecordingAnswerInterpreter(database_connection)

        def run_service_lab(action: ServiceLabAction) -> ServiceLabReport:
            return _report(action, healthy=healthy)

        dependencies = replace(
            _dependencies(database_connection, run_service_lab),
            tutor_client=tutor,
            answer_interpreter=interpreter,
        )
        handle_chat_request(_request(_SEMANTIC_ANSWER), dependencies)
        assert len(tutor.requests) == 1
        handle_chat_request(_request("now"), dependencies)
        handle_chat_request(_request(_SEMANTIC_ANSWER), dependencies)
        assert len(tutor.requests) == 2
        handle_chat_request(_request(f"answer {_SEMANTIC_ANSWER}"), dependencies)
        assert len(tutor.requests) == 2
        assert interpreter.requests == []

        healthy = True
        handle_chat_request(_request("check"), dependencies)
        handle_chat_request(
            _request(_SEMANTIC_ANSWER), replace(dependencies, service_lab_runner=None)
        )
        assert len(tutor.requests) == 3
        assert interpreter.requests == []
        assert (
            list_completed_objective_ids(database_connection, "alice", CATALOG.course.id, "S8")
            == prerequisites
        )

        handle_chat_request(_request(_SEMANTIC_ANSWER), dependencies)
        assert len(tutor.requests) == 3
        assert len(interpreter.requests) == 1
        assert interpreter.requests[0].answer == _SEMANTIC_ANSWER
        assert list_completed_objective_ids(
            database_connection, "alice", CATALOG.course.id, "S8"
        ) == prerequisites | {"break-and-read-error"}


@pytest.mark.parametrize("transport", ["public-cli", "irc", "no-capability"])
def test_service_lab_launch_requires_private_capable_cli(
    migrated_database_path: Path,
    transport: str,
) -> None:
    """Public chat, private IRC, and older CLI clients cannot reserve or execute faults."""

    def unexpected_runner(action: ServiceLabAction) -> ServiceLabReport:
        raise AssertionError(f"unexpected service action: {action}")

    with connect_database(migrated_database_path) as database_connection:
        prerequisites = _seed_s8_prerequisites(database_connection)
        dependencies = _dependencies(
            database_connection, None if transport == "no-capability" else unexpected_runner
        )
        for message in ("now", "next", f"answer {_SEMANTIC_ANSWER}"):
            response = handle_chat_request(
                ChatRequest(
                    context=(
                        IrcChatContext(nickname="alice", target="guide", reply_target="alice")
                        if transport == "irc"
                        else CliChatContext(username="alice", terminal=None)
                    ),
                    visibility="public" if transport == "public-cli" else "private",
                    text=message,
                ),
                dependencies,
            )
            assert "guide now" in response.text
        assert (
            get_attempt(
                database_connection, "alice", CATALOG.course.id, "S8", "break-and-read-error"
            )
            is None
        )
        assert (
            list_completed_objective_ids(database_connection, "alice", CATALOG.course.id, "S8")
            == prerequisites
        )
        assert total_score_for_course(database_connection, "alice", CATALOG.course.id) == 0


def test_service_lab_lost_response_recovers_persisted_run_without_new_injection(
    migrated_database_path: Path,
) -> None:
    """After a lost start response, reconnecting retries the same idempotency key."""
    actions: list[ServiceLabAction] = []
    injected_runs: list[str] = []
    with connect_database(migrated_database_path) as database_connection:
        prerequisites = _seed_s8_prerequisites(database_connection)

    def run_service_lab(action: ServiceLabAction) -> ServiceLabReport:
        assert not database_connection.in_transaction
        with connect_database(migrated_database_path) as observer:
            attempt = get_attempt(
                observer, "alice", CATALOG.course.id, "S8", "break-and-read-error"
            )
            assert attempt is not None
            assert attempt.run_id == action.run_id
        actions.append(action)
        if action.operation == "start" and action.run_id not in injected_runs:
            injected_runs.append(action.run_id)
            raise EOFError("private callback transport failure after injection")
        return _report(action, healthy=False)

    for request_number in range(3):
        with connect_database(migrated_database_path) as database_connection:
            response = handle_chat_request(
                _request("now"), _dependencies(database_connection, run_service_lab)
            )
            assert "private callback transport failure" not in response.text
            attempt = get_attempt(
                database_connection, "alice", CATALOG.course.id, "S8", "break-and-read-error"
            )
            assert attempt is not None
            assert attempt.run_id == actions[0].run_id
            assert (attempt.started_at is None) is (request_number == 0)
            assert (
                cast(
                    "tuple[int]",
                    database_connection.execute(
                        "select count(*) from service_lab_attempts"
                    ).fetchone(),
                )[0]
                == 1
            )
            assert (
                list_completed_objective_ids(database_connection, "alice", CATALOG.course.id, "S8")
                == prerequisites
            )
            assert total_score_for_course(database_connection, "alice", CATALOG.course.id) == 0
    assert [action.operation for action in actions] == ["start", "start", "inspect"]
    assert {action.run_id for action in actions} == {injected_runs[0]}
    assert len(injected_runs) == 1


def test_service_lab_existing_completion_does_not_backfill_new_challenges(
    migrated_database_path: Path,
) -> None:
    """The old objective remains complete, but each added challenge still needs its own run."""
    legacy_evidence = '{"validation_type":"command_history","passed":true}'
    with connect_database(migrated_database_path) as database_connection:
        prerequisites = _seed_s8_prerequisites(database_connection)
        complete_session_objective(
            database_connection,
            SessionObjectiveCompletion(
                handle="alice",
                course_id=CATALOG.course.id,
                session_id="S8",
                objective_id="break-and-read-error",
                completed_at="2026-09-26T09:30:00Z",
                evidence_json=legacy_evidence,
            ),
        )

    actions: list[ServiceLabAction] = []

    def run_service_lab(action: ServiceLabAction) -> ServiceLabReport:
        actions.append(action)
        return _report(action, healthy=False)

    with connect_database(migrated_database_path) as database_connection:
        current = current_session_objective(database_connection, CATALOG, handle="alice")
        assert current.objective is not None
        assert current.objective.id == "repair-service-arguments"
        handle_chat_request(_request("now"), _dependencies(database_connection, run_service_lab))
        assert len(actions) == 1
        assert actions[0].operation == "start"
        assert actions[0].scenario == "invalid-argument"
        assert (
            get_attempt(
                database_connection, "alice", CATALOG.course.id, "S8", "break-and-read-error"
            )
            is None
        )
        assert (
            get_attempt(
                database_connection, "alice", CATALOG.course.id, "S8", "repair-service-content"
            )
            is None
        )
        assert list_completed_objective_ids(
            database_connection, "alice", CATALOG.course.id, "S8"
        ) == prerequisites | {"break-and-read-error"}
        assert (
            cast(
                "tuple[str]",
                database_connection.execute(
                    """select evidence_json from session_objective_completions
                where handle = 'alice' and course_id = ? and session_id = 'S8'
                and objective_id = 'break-and-read-error'""",
                    (CATALOG.course.id,),
                ).fetchone(),
            )[0]
            == legacy_evidence
        )
        assert total_score_for_course(database_connection, "alice", CATALOG.course.id) == 0


def _seed_s8_prerequisites(database_connection: sqlite3.Connection) -> frozenset[str]:
    with database_connection:
        upsert_learner(
            database_connection,
            Learner(handle="alice", joined_at=_TIMESTAMP, tagline=None, created_at=_TIMESTAMP),
        )
        upsert_membership(
            database_connection,
            CohortMembership(handle="alice", course_id=CATALOG.course.id, joined_at=_TIMESTAMP),
        )
        upsert_course_release(
            database_connection,
            CourseRelease(
                course_id=CATALOG.course.id,
                session_reached="S8",
                released_at="2026-09-26T09:00:00Z",
            ),
        )
    current = current_session_objective(database_connection, CATALOG, handle="alice")
    assert current.session_id == "S8"
    assert current.objective is not None
    assert current.objective.id == "break-and-read-error"
    return list_completed_objective_ids(database_connection, "alice", CATALOG.course.id, "S8")


def _complete_objective(
    database_connection: sqlite3.Connection, objective_id: str, session_id: str = "S8"
) -> None:
    complete_session_objective(
        database_connection,
        SessionObjectiveCompletion(
            handle="alice",
            course_id=CATALOG.course.id,
            session_id=session_id,
            objective_id=objective_id,
            completed_at="2026-09-26T09:30:00Z",
            evidence_json="{}",
        ),
    )


def _request(text: str) -> ChatRequest:
    return ChatRequest(
        context=CliChatContext(username="alice", terminal="/dev/pts/1"),
        visibility="private",
        text=text,
    )


def _dependencies(
    database_connection: sqlite3.Connection,
    runner: Callable[[ServiceLabAction], ServiceLabReport] | None,
) -> ChatDependencies:
    return ChatDependencies(
        database_connection=database_connection,
        catalog=CATALOG,
        bot_name="guide-test",
        public_hostname="lf2607.kolamayermakers.org",
        timestamp_factory=lambda: _TIMESTAMP,
        service_lab_runner=runner,
    )


def _report(action: ServiceLabAction, *, healthy: bool) -> ServiceLabReport:
    return ServiceLabReport(
        run_id=action.run_id,
        scenario=action.scenario,
        started=True,
        healthy=healthy,
        unit="private unit diagnostic",
        status="active (running)" if healthy else "failed",
        journal="private journal diagnostic",
        http_status=200 if healthy else None,
    )


class _RecordingAnswerInterpreter:
    def __init__(
        self, database_connection: sqlite3.Connection, *, grading: str = "complete"
    ) -> None:
        self.database_connection = database_connection
        self.grading = grading
        self.requests: list[AnswerInterpretationRequest] = []

    def interpret_answer(self, request: AnswerInterpretationRequest) -> AnswerInterpretation:
        assert not self.database_connection.in_transaction
        self.requests.append(request)
        if self.grading == "error":
            raise TutorError("interpreter unavailable")
        components = tuple(
            AnswerComponentAnalysis(
                concept_id=rubric.concept_id,
                verdict=(
                    "contradicted"
                    if self.grading == "contradicted"
                    else "not_demonstrated"
                    if self.grading == "not-demonstrated"
                    else "demonstrated"
                ),
                evidence_quote=(
                    None
                    if self.grading == "not-demonstrated"
                    else "not in the answer"
                    if self.grading == "unmatched-quote"
                    else request.answer
                ),
            )
            for rubric in request.concept_rubrics
        )
        return AnswerInterpretation(
            components=components[:1]
            if self.grading == "partial"
            else (components[0], components[0])
            if self.grading == "duplicate"
            else components,
            feedback=None,
            provider="test",
            model="test-model",
            raw_arguments="{}",
        )


class _RecordingTutorClient:
    def __init__(self, database_connection: sqlite3.Connection) -> None:
        self.database_connection = database_connection
        self.requests: list[TutorRequest] = []

    def answer(
        self,
        tutor_request: TutorRequest,
        chunk_writer: Callable[[str], None] | None = None,
    ) -> TutorResponse:
        del chunk_writer
        assert not self.database_connection.in_transaction
        self.requests.append(tutor_request)
        return TutorResponse(
            text="Compare the current service status with its recent journal messages.",
            topic_tags=("service-lab",),
            model="test-model",
            provider="test",
        )
