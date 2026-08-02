"""Tests for deterministic validation evidence."""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from maker_guide import validation_paths
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.curriculum.models import (
    AllOfValidation,
    AnswerConcept,
    AnswerConceptAssessment,
    CommandHistoryValidation,
    ExecutablePathValidation,
    FileCheckValidation,
    InteractiveQuestionValidation,
    IrcChannelJoinObservedValidation,
    LearnerHandleQuestionValidation,
    PathExistsValidation,
    QuestValidation,
    SshPublicKeyObservedValidation,
    UserPortFileValidation,
)
from maker_guide.progress.validation import (
    QuestValidationInput,
    validate_quest,
    validate_session_objective,
    validation_failure_reasons,
    validation_support,
)
from maker_guide.repositories.audit_event import AuditEvent, append_audit_event
from maker_guide.repositories.command_observation import CommandObservation, add_command_observation
from maker_guide.repositories.helpers import connect_database
from maker_guide.validation_paths import UnixAccount, UnixAccountLookup
from tests.repositories.helpers import write_learner

_GENERIC_FALLBACK_ALLOWED_VALIDATION_FAILURE_REASONS = frozenset(
    {
        "incomplete-evidence",
        "unsupported-validation",
        "unknown-user",
        "unsafe-path",
        "path-escapes-scope",
        "broken-symlink",
        "symlink-loop",
        "permission-denied",
        "read-error",
        "not-regular-file",
        "file-too-large",
        "file-decode-error",
        "invalid-regex",
        "unsupported-port-formula",
    },
)


def test_command_history_validation_uses_sqlite_observations_not_audit(
    migrated_database_path: Path,
) -> None:
    """Audit rows cannot satisfy command-history validation evidence."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        append_audit_event(
            database_connection,
            AuditEvent(
                event_type="shell_observation",
                handle="alice",
                source="test",
                created_at="2026-07-19T09:00:00Z",
                payload={"commands": ["whoami", "date", "uptime"]},
            ),
        )

        failed_result = validate_quest(_validation_input(database_connection, "prove-shell-alive"))
        observation_ids = [
            add_command_observation(database_connection, _command_observation(command))
            for command in ("whoami", "date", "uptime")
        ]
        passed_result = validate_quest(_validation_input(database_connection, "prove-shell-alive"))

        assert failed_result.passed is False
        assert failed_result.failure_reason == "missing-command"
        assert failed_result.evidence == {
            "failure_reason": "missing-command",
            "matched_count": 0,
            "matched_commands": [],
            "matched_observation_ids": [],
            "missing_commands": ["whoami", "date", "uptime"],
            "observed_count": 0,
            "observed_since": "2026-07-19T09:00:00Z",
            "passed": False,
            "required_count": 3,
            "validation_type": "command_history",
        }
        assert passed_result.passed is True
        assert passed_result.failure_reason is None
        assert passed_result.evidence == {
            "failure_reason": None,
            "matched_count": 3,
            "matched_commands": ["whoami", "date", "uptime"],
            "matched_observation_ids": observation_ids,
            "missing_commands": [],
            "observed_count": 3,
            "observed_since": "2026-07-19T09:00:00Z",
            "passed": True,
            "required_count": 3,
            "validation_type": "command_history",
        }


def test_command_history_validation_uses_assignment_window(
    migrated_database_path: Path,
) -> None:
    """Commands observed before quest assignment do not satisfy command history checks."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        for command in ("whoami", "date", "uptime"):
            add_command_observation(database_connection, _command_observation(command))

        failed_result = validate_quest(
            _validation_input(
                database_connection,
                "prove-shell-alive",
                assigned_at="2026-07-19T09:01:00Z",
                checked_at="2026-07-19T09:03:00Z",
            ),
        )
        observation_ids = [
            add_command_observation(
                database_connection,
                _command_observation(command, observed_at="2026-07-19T09:02:00Z"),
            )
            for command in ("whoami", "date", "uptime")
        ]
        passed_result = validate_quest(
            _validation_input(
                database_connection,
                "prove-shell-alive",
                assigned_at="2026-07-19T09:01:00Z",
                checked_at="2026-07-19T09:03:00Z",
            ),
        )

    assert failed_result.passed is False
    assert failed_result.failure_reason == "missing-command"
    assert failed_result.evidence["observed_count"] == 0
    assert failed_result.evidence["observed_since"] == "2026-07-19T09:01:00Z"
    assert passed_result.passed is True
    assert passed_result.evidence["matched_observation_ids"] == observation_ids


def test_command_history_validation_excludes_observations_after_check(
    migrated_database_path: Path,
) -> None:
    """A future-dated command cannot satisfy an earlier deterministic check."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        for command in ("date", "uptime"):
            add_command_observation(
                database_connection,
                _command_observation(command, observed_at="2026-07-19T09:02:00Z"),
            )
        add_command_observation(
            database_connection,
            _command_observation("whoami", observed_at="2999-07-19T09:02:00Z"),
        )

        result = validate_quest(
            _validation_input(
                database_connection,
                "prove-shell-alive",
                assigned_at="2026-07-19T09:01:00Z",
                checked_at="2026-07-19T09:03:00Z",
            ),
        )

    assert result.passed is False
    assert result.evidence["matched_commands"] == ["date", "uptime"]
    assert result.evidence["missing_commands"] == ["whoami"]
    assert result.evidence["observed_count"] == 2


def test_audit_backed_validations_exclude_events_after_check(
    migrated_database_path: Path,
) -> None:
    """Future audit events cannot satisfy an earlier deterministic check."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        for audit_event in (
            AuditEvent(
                event_type="ssh_publickey_observed",
                handle="alice",
                source="test",
                created_at="2999-07-19T09:02:00Z",
                payload={"course_id": CATALOG.course.id},
            ),
            AuditEvent(
                event_type="irc_channel_joined",
                handle="alice",
                source="test",
                created_at="2999-07-19T09:02:00Z",
                payload={"channel": "#lf2607"},
            ),
            AuditEvent(
                event_type="irc_ctcp_version",
                handle="alice",
                source="test",
                created_at="2999-07-19T09:02:00Z",
                payload={"version": "WeeChat 4.4.0"},
            ),
        ):
            append_audit_event(
                database_connection,
                audit_event,
            )
        validation_input = QuestValidationInput(
            database_connection=database_connection,
            catalog=CATALOG,
            handle="alice",
            checked_at="2026-10-24T09:01:00Z",
            assigned_at="2026-07-19T09:00:00Z",
        )

        assert (
            validate_session_objective(
                validation_input,
                SshPublicKeyObservedValidation(),
            ).failure_reason
            == "missing-ssh-publickey"
        )
        assert (
            validate_session_objective(
                validation_input,
                IrcChannelJoinObservedValidation(channel="#lf2607"),
            ).failure_reason
            == "missing-irc-channel-join"
        )
        assert (
            validate_quest(
                replace(validation_input, quest=CATALOG.quest("use-terminal-irc")),
            ).failure_reason
            == "missing-irc-ctcp-version"
        )


def test_command_history_validation_groups_multi_command_pipeline_evidence(
    migrated_database_path: Path,
) -> None:
    """One observed pipeline can prove every command it contains."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        add_command_observation(database_connection, _command_observation("history | grep ssh"))
        result = validate_quest(
            QuestValidationInput(
                database_connection=database_connection,
                catalog=CATALOG,
                handle="alice",
                quest=replace(
                    CATALOG.quest("prove-shell-alive"),
                    validation=CommandHistoryValidation(
                        required_patterns=(r"^history \| grep ssh$",),
                        observed_commands=("history", "grep"),
                    ),
                ),
                checked_at="2026-07-19T09:00:00Z",
                assigned_at="2026-07-19T09:00:00Z",
            ),
        )

    assert result.passed is True
    assert result.evidence["matched_commands"] == ["history", "grep"]


def test_command_history_validation_is_unordered_by_default(
    migrated_database_path: Path,
) -> None:
    """Existing command checks accept required evidence in any chronological order."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        for command in ("uptime", "date", "whoami"):
            add_command_observation(database_connection, _command_observation(command))

        result = validate_quest(_validation_input(database_connection, "prove-shell-alive"))

    assert result.passed is True


def test_ordered_command_history_ignores_early_recovery_command(
    migrated_database_path: Path,
) -> None:
    """A cleanup before the tmux lifecycle cannot satisfy its final ordered step."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        add_command_observation(
            database_connection,
            _command_observation("tmux kill-session -t quest-workbench"),
        )
        lifecycle_observation_ids = [
            add_command_observation(database_connection, _command_observation(command))
            for command in (
                "tmux new -s quest-workbench",
                "tmux ls",
                "tmux attach -t quest-workbench",
            )
        ]

        failed_result = validate_quest(
            _validation_input(database_connection, "keep-tmux-workbench"),
        )
        final_kill_id = add_command_observation(
            database_connection,
            _command_observation("tmux kill-session -t quest-workbench"),
        )
        passed_result = validate_quest(
            _validation_input(database_connection, "keep-tmux-workbench"),
        )

    assert failed_result.passed is False
    assert failed_result.evidence["matched_count"] == 3
    assert passed_result.passed is True
    assert passed_result.evidence["matched_observation_ids"] == [
        *lifecycle_observation_ids,
        final_kill_id,
    ]


@pytest.mark.parametrize(
    ("objective_id", "answer_text", "failure_reason"),
    [
        (
            "make-first-pipe",
            "cut sends stdout into wc's stdin.",
            None,
        ),
        (
            "make-first-pipe",
            "cut's stdout becomes wc's stdin.",
            None,
        ),
        (
            "make-first-pipe",
            "stdout leaves cut, wc reads stdin",
            None,
        ),
        (
            "make-first-pipe",
            "stdout is descriptor 1 and stdin is descriptor 0.",
            "missing-concept",
        ),
        (
            "make-first-pipe",
            "cut writes stdout to the terminal; wc reads stdin from the keyboard.",
            "missing-concept",
        ),
        (
            "make-first-pipe",
            "cut never writes stdout and wc never reads stdin.",
            "contradicted-concept",
        ),
        (
            "name-stdout-descriptor",
            "stdout is descriptor 1.",
            None,
        ),
        (
            "name-stdout-descriptor",
            "stdout is descriptor 0.",
            "contradicted-concept",
        ),
        (
            "name-stdin-descriptor",
            "stdin is descriptor 0.",
            None,
        ),
        (
            "name-stdin-descriptor",
            "stdin is descriptor 1.",
            "contradicted-concept",
        ),
        (
            "combine-and-copy-streams",
            "stderr is descriptor 2.",
            None,
        ),
        (
            "combine-and-copy-streams",
            "2=stderr",
            None,
        ),
        (
            "combine-and-copy-streams",
            "stderr is descriptor 1.",
            "contradicted-concept",
        ),
        (
            "read-redirections-left-to-right",
            "The shell applies redirections left to right.",
            None,
        ),
        (
            "read-redirections-left-to-right",
            "The shell applies redirections right to left.",
            "contradicted-concept",
        ),
        (
            "route-stderr-to-stdout-destination",
            "2>&1 sends stderr to stdout's current destination.",
            None,
        ),
        (
            "route-stderr-to-stdout-destination",
            "2>&1 combines the streams.",
            "missing-concept",
        ),
        (
            "route-stderr-to-stdout-destination",
            "2>&1 sends stdout to stderr.",
            "contradicted-concept",
        ),
        (
            "read-process-table",
            "An executable is a program file stored on disk.",
            None,
        ),
        (
            "read-process-table",
            "An executable is never a file.",
            "contradicted-concept",
        ),
        (
            "describe-running-process",
            "A process is a running instance of a program.",
            None,
        ),
        (
            "describe-running-process",
            "A process is not a running instance.",
            "contradicted-concept",
        ),
        (
            "report-process-pair",
            "PID 4242, command bash.",
            None,
        ),
        (
            "report-process-pair",
            "PID 0, command bash.",
            "missing-concept",
        ),
        (
            "report-process-pair",
            "PID 4242 is not command bash.",
            "contradicted-concept",
        ),
    ],
)
def test_s3_answers_require_expected_concepts(
    migrated_database_path: Path,
    objective_id: str,
    answer_text: str,
    failure_reason: str | None,
) -> None:
    """S3 answers accept supported wording and reject missing or contradicted concepts."""
    objective_validation = next(
        objective.validation
        for objective in CATALOG.session("S3").objectives
        if objective.id == objective_id
    )
    assert isinstance(objective_validation, AllOfValidation)

    with connect_database(migrated_database_path) as database_connection:
        result = validate_session_objective(
            QuestValidationInput(
                database_connection=database_connection,
                catalog=CATALOG,
                handle="alice",
                checked_at="2026-08-01T09:00:00Z",
                assigned_at="2026-08-01T09:00:00Z",
                answer_text=answer_text,
            ),
            next(
                validation
                for validation in objective_validation.validations
                if isinstance(validation, InteractiveQuestionValidation)
            ),
        )

    assert result.passed is (failure_reason is None)
    assert result.failure_reason == failure_reason


def test_s3_separate_streams_rejects_crossed_contents(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Each separated stream file must contain only its own output."""
    learner_home = tmp_path / "alice"
    (learner_home / "playground").mkdir(parents=True)
    stdout_path = learner_home / "playground" / "stdout.txt"
    stderr_path = learner_home / "playground" / "stderr.txt"
    stdout_path.write_text(
        "/etc/hostname\nls: cannot access '/no/such/path': No such file or directory\n",
        encoding="utf-8",
    )
    stderr_path.write_text(
        "ls: cannot access '/no/such/path': No such file or directory\n",
        encoding="utf-8",
    )

    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        add_command_observation(
            database_connection,
            _command_observation(
                "cat /etc/hostname > /dev/null",
                observed_at="2026-08-01T09:01:00Z",
            ),
        )
        stream_objective = next(
            objective
            for objective in CATALOG.session("S3").objectives
            if objective.id == "separate-standard-streams"
        )
        validation_input = QuestValidationInput(
            database_connection=database_connection,
            catalog=CATALOG,
            handle="alice",
            checked_at="2026-08-01T09:02:00Z",
            assigned_at="2026-08-01T09:00:00Z",
            account_lookup=_account_lookup(learner_home),
        )

        stdout_crossed_result = validate_session_objective(
            validation_input,
            stream_objective.validation,
        )
        stdout_path.write_text("/etc/hostname\n", encoding="utf-8")
        stderr_path.write_text(
            "ls: cannot access '/no/such/path': No such file or directory\n/etc/hostname\n",
            encoding="utf-8",
        )
        stderr_crossed_result = validate_session_objective(
            validation_input,
            stream_objective.validation,
        )
        stderr_path.write_text(
            "ls: cannot access '/no/such/path': No such file or directory\n",
            encoding="utf-8",
        )
        passed_result = validate_session_objective(
            validation_input,
            stream_objective.validation,
        )

    assert stdout_crossed_result.failure_reason == "forbidden-content-present"
    assert stderr_crossed_result.failure_reason == "forbidden-content-present"
    assert passed_result.passed is True


def test_command_history_validation_canonicalizes_observed_command_whitespace(
    migrated_database_path: Path,
) -> None:
    """Legacy observations with irregular spacing satisfy exact command patterns."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        for command in (
            "head\t-n  5 /etc/services ",
            "tail   -n\t5  /etc/services",
        ):
            add_command_observation(database_connection, _command_observation(command))

        result = validate_quest(_validation_input(database_connection, "read-file-ends"))

    assert result.passed is True


def test_count_stream_accepts_pipeline_without_spaces_around_operators(
    migrated_database_path: Path,
) -> None:
    """A shell-valid pipeline does not require cosmetic spaces around pipes."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        add_command_observation(
            database_connection,
            _command_observation("cut -d: -f7 /etc/passwd|sort -u | wc -l"),
        )

        result = validate_quest(_validation_input(database_connection, "count-stream"))

    assert result.passed is True
    assert result.evidence["matched_commands"] == ["cut", "sort", "wc"]


def test_validation_support_reports_interactive_questions_as_supported() -> None:
    """Support introspection reports implemented interactive concept checks."""
    support = validation_support(CATALOG.quest("name-system").validation)

    assert support.supported is True
    assert support.unsupported_validation_types == ()


def test_validation_support_reports_file_matches_path_as_supported() -> None:
    """Support introspection reports exact file comparison as supported."""
    support = validation_support(CATALOG.quest("copy-and-inspect-ownership").validation)

    assert support.supported is True
    assert support.unsupported_validation_types == ()


def test_validation_support_reports_irc_ctcp_version_as_supported() -> None:
    """Support introspection reports IRC CTCP VERSION checks as supported."""
    support = validation_support(CATALOG.quest("use-terminal-irc").validation)

    assert support.supported is True
    assert support.unsupported_validation_types == ()


def test_quest_failure_feedback_reasons_are_emitted_by_validation() -> None:
    """Catalog-specific feedback must refer to real emitted validation reasons."""
    for quest in CATALOG.course.quests:
        feedback_reasons = frozenset(
            feedback_item.reason for feedback_item in quest.failure_feedback
        )
        assert feedback_reasons <= validation_failure_reasons(quest.validation), quest.id


def test_actionable_validation_failure_reasons_have_quest_feedback() -> None:
    """Learner-actionable runtime failures need exact quest-specific recovery copy."""
    for quest in CATALOG.course.quests:
        feedback_reasons = frozenset(
            feedback_item.reason for feedback_item in quest.failure_feedback
        )
        missing_feedback_reasons = validation_failure_reasons(quest.validation) - (
            feedback_reasons | _GENERIC_FALLBACK_ALLOWED_VALIDATION_FAILURE_REASONS
        )
        assert not missing_feedback_reasons, quest.id


def test_validation_support_treats_filesystem_validators_as_supported() -> None:
    """Filesystem-backed validation leaves have deterministic runtime support."""
    support = validation_support(
        AllOfValidation(
            validations=(
                PathExistsValidation(paths=("~/public_html/index.html",)),
                ExecutablePathValidation(paths=("~/bin/run",)),
                FileCheckValidation(path="~/notes.txt", required_regex=r"ready"),
                UserPortFileValidation(path="~/site.service", required_regex_template=r"{port}"),
            ),
        ),
    )

    assert support.supported is True
    assert support.unsupported_validation_types == ()


def test_validation_failure_reasons_are_instance_specific() -> None:
    """Optional forbidden checks only appear when the validation instance can emit them."""
    assert "forbidden-content-present" not in validation_failure_reasons(
        FileCheckValidation(path="~/notes.txt", required_regex=r"ready"),
    )
    assert "forbidden-content-present" in validation_failure_reasons(
        FileCheckValidation(
            path="~/notes.txt",
            required_regex=r"ready",
            forbidden_regex=r"draft",
        ),
    )
    assert "contradicted-concept" not in validation_failure_reasons(
        InteractiveQuestionValidation(
            question="What matters?",
            required_concepts=(
                AnswerConcept(id="ready", aliases=(r"\bready\b",), rubric="Answer says ready."),
            ),
        ),
    )
    assert "contradicted-concept" in validation_failure_reasons(
        InteractiveQuestionValidation(
            question="What matters?",
            required_concepts=(
                AnswerConcept(
                    id="ready",
                    aliases=(r"\bready\b",),
                    rubric="Answer says ready.",
                    forbidden_patterns=(r"\bnot ready\b",),
                ),
            ),
        ),
    )
    assert "unsupported-port-formula" not in validation_failure_reasons(
        UserPortFileValidation(path="~/site.service", required_regex_template=r"{port}"),
    )


def test_irc_ctcp_version_validation_accepts_terminal_clients(
    migrated_database_path: Path,
) -> None:
    """IRC CTCP VERSION evidence passes for accepted terminal clients."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        audit_event_id = append_audit_event(
            database_connection,
            AuditEvent(
                event_type="irc_ctcp_version",
                handle="alice",
                source="irc-bot",
                created_at="2026-10-24T09:01:00Z",
                payload={"nick": "alice", "version": "WeeChat 4.4.0"},
            ),
        )

        result = validate_quest(
            _validation_input(
                database_connection,
                "use-terminal-irc",
                assigned_at="2026-10-24T09:00:00Z",
                checked_at="2026-10-24T09:02:00Z",
            ),
        )

    assert result.passed is True
    assert result.failure_reason is None
    assert result.evidence == {
        "accepted_clients": ["WeeChat", "irssi", "BitchX"],
        "audit_event_id": audit_event_id,
        "failure_reason": None,
        "passed": True,
        "validation_type": "irc_ctcp_version",
        "version": "WeeChat 4.4.0",
    }


def test_irc_ctcp_version_validation_rejects_browser_clients(
    migrated_database_path: Path,
) -> None:
    """IRC CTCP VERSION evidence fails for browser clients such as Gamja."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        append_audit_event(
            database_connection,
            AuditEvent(
                event_type="irc_ctcp_version",
                handle="alice",
                source="irc-bot",
                created_at="2026-10-24T09:01:00Z",
                payload={"nick": "alice", "version": "Gamja web IRC"},
            ),
        )

        result = validate_quest(
            _validation_input(
                database_connection,
                "use-terminal-irc",
                assigned_at="2026-10-24T09:00:00Z",
                checked_at="2026-10-24T09:02:00Z",
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "unsupported-irc-client"
    assert result.evidence["version"] == "Gamja web IRC"


def test_irc_ctcp_version_validation_requires_recent_evidence(
    migrated_database_path: Path,
) -> None:
    """IRC CTCP VERSION evidence must be recorded after quest assignment."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        append_audit_event(
            database_connection,
            AuditEvent(
                event_type="irc_ctcp_version",
                handle="alice",
                source="irc-bot",
                created_at="2026-10-24T08:59:00Z",
                payload={"nick": "alice", "version": "irssi 1.4.5"},
            ),
        )

        result = validate_quest(
            _validation_input(
                database_connection,
                "use-terminal-irc",
                assigned_at="2026-10-24T09:00:00Z",
                checked_at="2026-10-24T09:02:00Z",
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "missing-irc-ctcp-version"


def test_interactive_question_validation_matches_required_concepts(
    migrated_database_path: Path,
) -> None:
    """Interactive answers pass when every required concept matches."""
    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _answer_validation_input(
                database_connection,
                _interactive_validation(),
                "The HOSTNAME and PORT identify the socket endpoint.",
            ),
        )

    assert result.passed is True
    assert result.failure_reason is None
    assert result.evidence == {
        "answer_present": True,
        "contradicted_concept_count": 0,
        "contradicted_concept_ids": [],
        "expected_concept_count": 2,
        "failure_reason": None,
        "matched_concept_count": 2,
        "matched_concept_ids": ["host", "port"],
        "missing_concept_ids": [],
        "passed": True,
        "validation_type": "interactive_question",
    }


def test_interactive_question_validation_reports_missing_concept(
    migrated_database_path: Path,
) -> None:
    """Missing concepts fail without storing raw answers or alias regexes."""
    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _answer_validation_input(
                database_connection,
                _interactive_validation(),
                "The host identifies the server.",
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "missing-concept"
    assert result.evidence["matched_concept_ids"] == ["host"]
    assert result.evidence["missing_concept_ids"] == ["port"]
    assert "server" not in str(result.evidence)
    assert "hostname" not in str(result.evidence)


def test_interactive_question_validation_reports_contradicted_concept(
    migrated_database_path: Path,
) -> None:
    """Forbidden patterns block false positives such as negated concepts."""
    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _answer_validation_input(
                database_connection,
                _interactive_validation(),
                "I did not use hostname, but I used a port.",
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "contradicted-concept"
    assert result.evidence["matched_concept_ids"] == ["host", "port"]
    assert result.evidence["contradicted_concept_ids"] == ["host"]
    assert result.evidence["missing_concept_ids"] == []


def test_semantic_assessment_cannot_override_deterministic_contradiction(
    migrated_database_path: Path,
) -> None:
    """Provider demonstrations cannot override explicit forbidden answer text."""
    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _answer_validation_input(
                database_connection,
                _interactive_validation(),
                "I did not use hostname, but I used a port.",
                assessments=(
                    AnswerConceptAssessment(concept_id="host", verdict="demonstrated"),
                    AnswerConceptAssessment(concept_id="port", verdict="demonstrated"),
                ),
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "contradicted-concept"
    assert result.evidence["contradicted_concept_ids"] == ["host"]


def test_interactive_question_validation_requires_answer(
    migrated_database_path: Path,
) -> None:
    """Empty answers fail before concept checks."""
    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _answer_validation_input(database_connection, _interactive_validation(), "  \n  "),
        )

    assert result.passed is False
    assert result.failure_reason == "missing-answer"
    assert result.evidence == {
        "answer_present": False,
        "contradicted_concept_count": 0,
        "contradicted_concept_ids": [],
        "expected_concept_count": 2,
        "failure_reason": "missing-answer",
        "matched_concept_count": 0,
        "matched_concept_ids": [],
        "missing_concept_ids": ["host", "port"],
        "passed": False,
        "validation_type": "interactive_question",
    }


@pytest.mark.parametrize(
    "answer_text",
    ["6", "found 6", "i did run ls -la ~ and i found 6 things"],
)
def test_count_home_entries_accepts_plain_count_answers(
    migrated_database_path: Path,
    answer_text: str,
) -> None:
    """The home-entry count quest should not require magic wording."""
    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _validation_input(
                database_connection,
                "count-home-entries",
                answer_text=answer_text,
            ),
        )

    assert result.passed is True


def test_learner_handle_question_validation_matches_handle(
    migrated_database_path: Path,
) -> None:
    """Learner-handle answers pass only when they match the current handle."""
    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _answer_validation_input(
                database_connection,
                LearnerHandleQuestionValidation(question="Who owns the file?"),
                "  Alice  ",
            ),
        )

    assert result.passed is True
    assert result.failure_reason is None
    assert result.evidence == {
        "answer_present": True,
        "expected_handle_matched": True,
        "failure_reason": None,
        "passed": True,
        "validation_type": "learner_handle_question",
    }
    assert "Alice" not in str(result.evidence)


@pytest.mark.parametrize(
    ("answer_text", "failure_reason", "answer_present", "expected_handle_matched"),
    [
        ("  \n  ", "missing-answer", False, False),
        ("root", "wrong-answer", True, False),
        ("/home/alice", "wrong-answer", True, False),
        ("~alice", "wrong-answer", True, False),
    ],
)
def test_learner_handle_question_validation_reports_failed_answers(
    migrated_database_path: Path,
    answer_text: str,
    failure_reason: str,
    answer_present: bool,
    expected_handle_matched: bool,
) -> None:
    """Blank and non-handle owner answers fail without storing answer text."""
    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _answer_validation_input(
                database_connection,
                LearnerHandleQuestionValidation(question="Who owns the file?"),
                answer_text,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == failure_reason
    assert result.evidence == {
        "answer_present": answer_present,
        "expected_handle_matched": expected_handle_matched,
        "failure_reason": failure_reason,
        "passed": False,
        "validation_type": "learner_handle_question",
    }
    if answer_text.strip():
        assert answer_text.strip() not in str(result.evidence)


def test_path_exists_validation_resolves_catalog_paths(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Path existence checks use learner-home, relative, and absolute catalog paths."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    index_file = learner_home / "public_html" / "index.html"
    index_file.parent.mkdir()
    index_file.write_text("<h1>Hi</h1>", encoding="utf-8")
    absolute_file = tmp_path / "system-state.txt"
    absolute_file.write_text("ready", encoding="utf-8")

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                PathExistsValidation(
                    paths=(
                        "~/public_html/index.html",
                        "public_html/index.html",
                        str(absolute_file),
                    ),
                ),
                learner_home,
            ),
        )

    assert result.passed is True
    assert result.failure_reason is None
    assert result.evidence == {
        "existing_count": 3,
        "failure_reason": None,
        "passed": True,
        "paths": [
            {
                "catalog_path": "~/public_html/index.html",
                "passed": True,
                "failure_reason": None,
            },
            {
                "catalog_path": "public_html/index.html",
                "passed": True,
                "failure_reason": None,
            },
            {"catalog_path": str(absolute_file), "passed": True, "failure_reason": None},
        ],
        "required_count": 3,
        "validation_type": "path_exists",
    }


def test_path_exists_validation_reports_missing_path(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """A missing target fails with the shared path-resolution reason."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                PathExistsValidation(paths=("missing.txt",)),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "missing-path"
    assert result.evidence == {
        "existing_count": 0,
        "failure_reason": "missing-path",
        "passed": False,
        "paths": [
            {
                "catalog_path": "missing.txt",
                "passed": False,
                "failure_reason": "missing-path",
            },
        ],
        "required_count": 1,
        "validation_type": "path_exists",
    }


def test_path_exists_validation_reports_unsafe_path(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Unsafe traversal is rejected before filesystem resolution."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                PathExistsValidation(paths=("../secret.txt",)),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "unsafe-path"
    assert result.evidence["paths"] == [
        {
            "catalog_path": "../secret.txt",
            "passed": False,
            "failure_reason": "unsafe-path",
        },
    ]


def test_path_exists_validation_reports_unknown_user(
    migrated_database_path: Path,
) -> None:
    """Missing Unix accounts fail as structured learner-facing evidence."""
    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            QuestValidationInput(
                database_connection=database_connection,
                catalog=CATALOG,
                handle="alice",
                quest=replace(
                    CATALOG.quest("prove-shell-alive"),
                    validation=PathExistsValidation(paths=("ready.txt",)),
                ),
                checked_at="2026-07-19T09:00:00Z",
                assigned_at="2026-07-19T09:00:00Z",
                account_lookup=_unknown_account_lookup,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "unknown-user"
    assert result.evidence["paths"] == [
        {
            "catalog_path": "ready.txt",
            "passed": False,
            "failure_reason": "unknown-user",
        },
    ]


def test_path_exists_validation_accepts_in_scope_symlink(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Symlinks count when their resolved target stays inside learner home."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    target_file = learner_home / "target.txt"
    target_file.write_text("ready", encoding="utf-8")
    (learner_home / "target-link.txt").symlink_to(target_file)

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                PathExistsValidation(paths=("target-link.txt",)),
                learner_home,
            ),
        )

    assert result.passed is True
    assert result.failure_reason is None
    assert result.evidence["existing_count"] == 1
    assert result.evidence["paths"] == [
        {
            "catalog_path": "target-link.txt",
            "passed": True,
            "failure_reason": None,
        },
    ]


def test_path_exists_validation_reports_symlink_escape(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Learner-home declarations cannot escape through symlinks."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("outside", encoding="utf-8")
    (learner_home / "outside-link.txt").symlink_to(outside_file)

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                PathExistsValidation(paths=("outside-link.txt",)),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "path-escapes-scope"
    assert result.evidence["paths"] == [
        {
            "catalog_path": "outside-link.txt",
            "passed": False,
            "failure_reason": "path-escapes-scope",
        },
    ]


def test_path_exists_validation_reports_broken_symlink(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Broken symlinks do not satisfy path-existence checks."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    (learner_home / "broken-link.txt").symlink_to(learner_home / "missing.txt")

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                PathExistsValidation(paths=("broken-link.txt",)),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "broken-symlink"
    assert result.evidence["paths"] == [
        {
            "catalog_path": "broken-link.txt",
            "passed": False,
            "failure_reason": "broken-symlink",
        },
    ]


def test_path_exists_validation_reports_symlink_loop(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Symlink loops fail with stable validation evidence."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    first_link = learner_home / "link-one.txt"
    second_link = learner_home / "link-two.txt"
    first_link.symlink_to(second_link)
    second_link.symlink_to(first_link)

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                PathExistsValidation(paths=("link-one.txt",)),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "symlink-loop"
    assert result.evidence["paths"] == [
        {
            "catalog_path": "link-one.txt",
            "passed": False,
            "failure_reason": "symlink-loop",
        },
    ]


def test_path_exists_validation_reports_permission_denied(
    migrated_database_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Permission errors stay structured for path-existence checks."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    secret_file = learner_home / "secret.txt"
    secret_file.write_text("secret", encoding="utf-8")
    original_resolve = Path.resolve

    def resolve_with_permission_error(path: Path, *, strict: bool = False) -> Path:
        if path == secret_file:
            raise PermissionError
        return original_resolve(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", resolve_with_permission_error)

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                PathExistsValidation(paths=("secret.txt",)),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "permission-denied"
    assert result.evidence["paths"] == [
        {
            "catalog_path": "secret.txt",
            "passed": False,
            "failure_reason": "permission-denied",
        },
    ]


def test_file_check_validation_reads_bounded_text_files(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """File checks match required regexes and store bounded non-content evidence."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    notes_file = learner_home / "notes.txt"
    notes_file.write_text("ready\n", encoding="utf-8")

    with connect_database(migrated_database_path) as database_connection:
        passed_result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                FileCheckValidation(path="notes.txt", required_regex=r"^ready$"),
                learner_home,
            ),
        )
        failed_result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                FileCheckValidation(path="notes.txt", required_regex=r"missing"),
                learner_home,
            ),
        )

    assert passed_result.passed is True
    assert passed_result.evidence == {
        "byte_count": 6,
        "catalog_path": "notes.txt",
        "failure_reason": None,
        "forbidden_matched": None,
        "passed": True,
        "path_category": "learner-relative",
        "required_matched": True,
        "validation_type": "file_check",
    }
    assert "file_contents" not in passed_result.evidence
    assert failed_result.passed is False
    assert failed_result.failure_reason == "file-content-mismatch"
    assert failed_result.evidence == {
        "byte_count": 6,
        "catalog_path": "notes.txt",
        "failure_reason": "file-content-mismatch",
        "forbidden_matched": None,
        "passed": False,
        "path_category": "learner-relative",
        "required_matched": False,
        "validation_type": "file_check",
    }


def test_file_check_validation_reports_missing_path(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Missing file targets use the shared path-resolution failure reason."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                FileCheckValidation(path="missing.txt", required_regex=r"ready"),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "missing-path"
    assert result.evidence == {
        "catalog_path": "missing.txt",
        "failure_reason": "missing-path",
        "passed": False,
        "path_category": "learner-relative",
        "validation_type": "file_check",
    }


def test_file_check_validation_rejects_symlink_swap_escape_before_read(
    migrated_database_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """File checks reject descriptors that escape home after stale path resolution."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    inside_file = learner_home / "notes.txt"
    inside_file.write_text("ready\n", encoding="utf-8")
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("secret\n", encoding="utf-8")
    link_path = learner_home / "notes-link.txt"
    link_path.symlink_to(inside_file)
    original_open = validation_paths.os.open

    def open_after_symlink_swap(path: Path, flags: int) -> int:
        if path == link_path:
            link_path.unlink()
            link_path.symlink_to(outside_file)
        return original_open(path, flags)

    monkeypatch.setattr(validation_paths.os, "open", open_after_symlink_swap)

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                FileCheckValidation(path="notes-link.txt", required_regex=r"secret"),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "path-escapes-scope"
    assert result.evidence == {
        "catalog_path": "notes-link.txt",
        "failure_reason": "path-escapes-scope",
        "passed": False,
        "path_category": "learner-relative",
        "validation_type": "file_check",
    }


def test_file_check_validation_rejects_forbidden_content(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Forbidden file regexes fail even when the required regex matches."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    notes_file = learner_home / "notes.txt"
    notes_file.write_text("ready\nsecret\n", encoding="utf-8")

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                FileCheckValidation(
                    path="notes.txt",
                    required_regex=r"ready",
                    forbidden_regex=r"secret",
                ),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "forbidden-content-present"
    assert result.evidence["required_matched"] is True
    assert result.evidence["forbidden_matched"] is True


def test_file_check_validation_requires_regular_utf8_file(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Directories and non-UTF-8 files do not satisfy content validation."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    invalid_text_file = learner_home / "invalid.txt"
    invalid_text_file.write_bytes(b"\xff")

    with connect_database(migrated_database_path) as database_connection:
        directory_result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                FileCheckValidation(path="~", required_regex=r"ready"),
                learner_home,
            ),
        )
        invalid_text_result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                FileCheckValidation(path="invalid.txt", required_regex=r"ready"),
                learner_home,
            ),
        )

    assert directory_result.passed is False
    assert directory_result.failure_reason == "not-regular-file"
    assert invalid_text_result.passed is False
    assert invalid_text_result.failure_reason == "file-decode-error"


def test_file_check_validation_reports_permission_denied(
    migrated_database_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Permission errors stay structured instead of leaking filesystem exceptions."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    secret_file = learner_home / "secret.txt"
    secret_file.write_text("secret", encoding="utf-8")
    original_resolve = Path.resolve

    def resolve_with_permission_error(path: Path, *, strict: bool = False) -> Path:
        if path == secret_file:
            raise PermissionError
        return original_resolve(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", resolve_with_permission_error)

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                FileCheckValidation(path="secret.txt", required_regex=r"secret"),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "permission-denied"
    assert result.evidence == {
        "catalog_path": "secret.txt",
        "failure_reason": "permission-denied",
        "passed": False,
        "path_category": "learner-relative",
        "validation_type": "file_check",
    }


def test_file_check_validation_rejects_large_files(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Oversized files fail without reading unbounded content into evidence."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    large_file = learner_home / "large.txt"
    file_size_over_validation_limit = 1_048_577
    large_file.write_bytes(b"x" * file_size_over_validation_limit)

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                FileCheckValidation(path="large.txt", required_regex=r"x"),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "file-too-large"
    assert result.evidence == {
        "byte_count": file_size_over_validation_limit,
        "catalog_path": "large.txt",
        "failure_reason": "file-too-large",
        "passed": False,
        "path_category": "learner-relative",
        "validation_type": "file_check",
    }
    assert "file_contents" not in result.evidence


def test_file_check_validation_reports_runtime_invalid_regex(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Runtime regex errors are still reported defensively if a bad rule reaches validation."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    notes_file = learner_home / "notes.txt"
    notes_file.write_text("ready\n", encoding="utf-8")

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                FileCheckValidation(path="notes.txt", required_regex="("),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "invalid-regex"
    assert result.evidence == {
        "byte_count": 6,
        "catalog_path": "notes.txt",
        "failure_reason": "invalid-regex",
        "passed": False,
        "path_category": "learner-relative",
        "validation_type": "file_check",
    }


def test_composite_validation_combines_file_check_and_command_history(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """All-of validation can combine file content with observed command evidence."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    notes_file = learner_home / "notes.txt"
    notes_file.write_text("ready\n", encoding="utf-8")

    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        observation_id = add_command_observation(
            database_connection,
            _command_observation("cat notes.txt"),
        )
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                AllOfValidation(
                    validations=(
                        CommandHistoryValidation(
                            required_patterns=(r"^cat notes\.txt$",),
                            observed_commands=("cat",),
                        ),
                        FileCheckValidation(path="notes.txt", required_regex=r"^ready$"),
                    ),
                ),
                learner_home,
            ),
        )

    assert result.passed is True
    assert result.failure_reason is None
    assert result.evidence["validation_type"] == "all_of"
    assert result.evidence["checks"] == [
        {
            "failure_reason": None,
            "matched_count": 1,
            "matched_commands": ["cat"],
            "matched_observation_ids": [observation_id],
            "missing_commands": [],
            "observed_count": 1,
            "observed_since": "2026-07-19T09:00:00Z",
            "passed": True,
            "required_count": 1,
            "validation_type": "command_history",
        },
        {
            "byte_count": 6,
            "catalog_path": "notes.txt",
            "failure_reason": None,
            "forbidden_matched": None,
            "passed": True,
            "path_category": "learner-relative",
            "required_matched": True,
            "validation_type": "file_check",
        },
    ]


def test_composite_validation_combines_file_check_and_executable_path(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Script quests can require exact file content and owner executable permission."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    script_file = learner_home / "run.sh"
    script_file.write_text("#!/bin/sh\nprintf 'hello makers\\n'\n", encoding="utf-8")
    script_file.chmod(0o700)

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                AllOfValidation(
                    validations=(
                        FileCheckValidation(
                            path="run.sh",
                            required_regex=r"(?s)^#!/bin/sh\nprintf 'hello makers\\n'\n$",
                        ),
                        ExecutablePathValidation(paths=("run.sh",)),
                    ),
                ),
                learner_home,
                user_id=script_file.stat().st_uid,
            ),
        )

    assert result.passed is True
    assert result.failure_reason is None
    assert result.evidence["checks"] == [
        {
            "byte_count": 34,
            "catalog_path": "run.sh",
            "failure_reason": None,
            "forbidden_matched": None,
            "passed": True,
            "path_category": "learner-relative",
            "required_matched": True,
            "validation_type": "file_check",
        },
        {
            "executable_count": 1,
            "failure_reason": None,
            "passed": True,
            "paths": [
                {
                    "catalog_path": "run.sh",
                    "passed": True,
                    "failure_reason": None,
                },
            ],
            "required_count": 1,
            "validation_type": "executable_path",
        },
    ]


def test_executable_path_validation_checks_owner_execute_bit(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Executable checks require regular files with the owner execute bit."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    script_file = learner_home / "run.sh"
    script_file.write_text("#!/bin/sh\n", encoding="utf-8")
    script_file.chmod(0o700)

    with connect_database(migrated_database_path) as database_connection:
        passed_result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                ExecutablePathValidation(paths=("run.sh",)),
                learner_home,
                user_id=script_file.stat().st_uid,
            ),
        )
        script_file.chmod(0o600)
        failed_result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                ExecutablePathValidation(paths=("run.sh",)),
                learner_home,
                user_id=script_file.stat().st_uid,
            ),
        )
        directory_result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                ExecutablePathValidation(paths=("~",)),
                learner_home,
                user_id=script_file.stat().st_uid,
            ),
        )

    assert passed_result.passed is True
    assert passed_result.evidence == {
        "executable_count": 1,
        "failure_reason": None,
        "passed": True,
        "paths": [
            {
                "catalog_path": "run.sh",
                "passed": True,
                "failure_reason": None,
            },
        ],
        "required_count": 1,
        "validation_type": "executable_path",
    }
    assert failed_result.passed is False
    assert failed_result.failure_reason == "not-executable"
    assert failed_result.evidence == {
        "executable_count": 0,
        "failure_reason": "not-executable",
        "passed": False,
        "paths": [
            {
                "catalog_path": "run.sh",
                "passed": False,
                "failure_reason": "not-executable",
            },
        ],
        "required_count": 1,
        "validation_type": "executable_path",
    }
    assert directory_result.passed is False
    assert directory_result.failure_reason == "not-regular-file"
    assert directory_result.evidence["paths"] == [
        {
            "catalog_path": "~",
            "passed": False,
            "failure_reason": "not-regular-file",
        },
    ]


def test_executable_path_validation_requires_learner_owned_file(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Owner execute only counts when the executable is owned by the learner."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    script_file = learner_home / "run.sh"
    script_file.write_text("#!/bin/sh\n", encoding="utf-8")
    script_file.chmod(0o700)

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                ExecutablePathValidation(paths=("run.sh",)),
                learner_home,
                user_id=script_file.stat().st_uid + 1,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "wrong-owner"
    assert result.evidence["paths"] == [
        {
            "catalog_path": "run.sh",
            "passed": False,
            "failure_reason": "wrong-owner",
        },
    ]


def test_ownership_proof_requires_owned_matching_file(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Ownership proof requires a matching learner-owned regular file."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    playground_path = learner_home / "playground"
    playground_path.mkdir()
    hostname_path = playground_path / "hostname"

    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        missing_path_result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                CATALOG.quest("copy-and-inspect-ownership").validation,
                learner_home,
                answer_text="alice",
            ),
        )
        hostname_path.mkdir()
        directory_result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                CATALOG.quest("copy-and-inspect-ownership").validation,
                learner_home,
                answer_text="alice",
            ),
        )
        hostname_path.rmdir()
        hostname_path.write_bytes(Path("/etc/hostname").read_bytes())
        wrong_uid_result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                CATALOG.quest("copy-and-inspect-ownership").validation,
                learner_home,
                user_id=hostname_path.stat().st_uid + 1,
                answer_text="alice",
            ),
        )
        hostname_path.write_text("different\n", encoding="utf-8")
        mismatched_content_result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                CATALOG.quest("copy-and-inspect-ownership").validation,
                learner_home,
                user_id=hostname_path.stat().st_uid,
            ),
        )
        hostname_path.write_bytes(Path("/etc/hostname").read_bytes())
        passed_result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                CATALOG.quest("copy-and-inspect-ownership").validation,
                learner_home,
                user_id=hostname_path.stat().st_uid,
            ),
        )

    assert missing_path_result.failure_reason == "missing-path"
    assert directory_result.failure_reason == "not-regular-file"
    assert wrong_uid_result.failure_reason == "wrong-owner"
    assert mismatched_content_result.failure_reason == "file-content-mismatch"
    assert passed_result.passed is True


def test_executable_path_validation_reports_missing_path(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Missing executable targets fail with the shared path-resolution reason."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                ExecutablePathValidation(paths=("missing.sh",)),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "missing-path"
    assert result.evidence == {
        "executable_count": 0,
        "failure_reason": "missing-path",
        "passed": False,
        "paths": [
            {
                "catalog_path": "missing.sh",
                "passed": False,
                "failure_reason": "missing-path",
            },
        ],
        "required_count": 1,
        "validation_type": "executable_path",
    }


def test_executable_path_validation_reports_unsafe_path(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Unsafe traversal is rejected before executable-bit inspection."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                ExecutablePathValidation(paths=("../run.sh",)),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "unsafe-path"
    assert result.evidence["paths"] == [
        {
            "catalog_path": "../run.sh",
            "passed": False,
            "failure_reason": "unsafe-path",
        },
    ]


def test_executable_path_validation_reports_unknown_user(
    migrated_database_path: Path,
) -> None:
    """Missing Unix accounts fail as structured executable validation evidence."""
    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            QuestValidationInput(
                database_connection=database_connection,
                catalog=CATALOG,
                handle="alice",
                quest=replace(
                    CATALOG.quest("prove-shell-alive"),
                    validation=ExecutablePathValidation(paths=("run.sh",)),
                ),
                checked_at="2026-07-19T09:00:00Z",
                assigned_at="2026-07-19T09:00:00Z",
                account_lookup=_unknown_account_lookup,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "unknown-user"
    assert result.evidence["paths"] == [
        {
            "catalog_path": "run.sh",
            "passed": False,
            "failure_reason": "unknown-user",
        },
    ]


def test_executable_path_validation_accepts_in_scope_symlink(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Executable symlinks pass when their target stays inside learner home."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    script_file = learner_home / "run.sh"
    script_file.write_text("#!/bin/sh\n", encoding="utf-8")
    script_file.chmod(0o700)
    (learner_home / "run-link.sh").symlink_to(script_file)

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                ExecutablePathValidation(paths=("run-link.sh",)),
                learner_home,
                user_id=script_file.stat().st_uid,
            ),
        )

    assert result.passed is True
    assert result.failure_reason is None
    assert result.evidence["executable_count"] == 1
    assert result.evidence["paths"] == [
        {
            "catalog_path": "run-link.sh",
            "passed": True,
            "failure_reason": None,
        },
    ]


def test_executable_path_validation_reports_symlink_escape(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Learner-home executable symlinks cannot escape learner-home scope."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    outside_script = tmp_path / "outside.sh"
    outside_script.write_text("#!/bin/sh\n", encoding="utf-8")
    outside_script.chmod(0o700)
    (learner_home / "outside-link.sh").symlink_to(outside_script)

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                ExecutablePathValidation(paths=("outside-link.sh",)),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "path-escapes-scope"
    assert result.evidence["paths"] == [
        {
            "catalog_path": "outside-link.sh",
            "passed": False,
            "failure_reason": "path-escapes-scope",
        },
    ]


def test_executable_path_validation_reports_broken_symlink(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Broken executable symlinks do not satisfy executable checks."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    (learner_home / "broken-link.sh").symlink_to(learner_home / "missing.sh")

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                ExecutablePathValidation(paths=("broken-link.sh",)),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "broken-symlink"
    assert result.evidence["paths"] == [
        {
            "catalog_path": "broken-link.sh",
            "passed": False,
            "failure_reason": "broken-symlink",
        },
    ]


def test_executable_path_validation_reports_symlink_loop(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Executable symlink loops fail with stable validation evidence."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    first_link = learner_home / "link-one.sh"
    second_link = learner_home / "link-two.sh"
    first_link.symlink_to(second_link)
    second_link.symlink_to(first_link)

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                ExecutablePathValidation(paths=("link-one.sh",)),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "symlink-loop"
    assert result.evidence["paths"] == [
        {
            "catalog_path": "link-one.sh",
            "passed": False,
            "failure_reason": "symlink-loop",
        },
    ]


def test_executable_path_validation_reports_permission_denied(
    migrated_database_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Permission errors stay structured for executable checks."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    script_file = learner_home / "secret.sh"
    script_file.write_text("#!/bin/sh\n", encoding="utf-8")
    script_file.chmod(0o700)
    original_resolve = Path.resolve

    def resolve_with_permission_error(path: Path, *, strict: bool = False) -> Path:
        if path == script_file:
            raise PermissionError
        return original_resolve(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", resolve_with_permission_error)

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                ExecutablePathValidation(paths=("secret.sh",)),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "permission-denied"
    assert result.evidence["paths"] == [
        {
            "catalog_path": "secret.sh",
            "passed": False,
            "failure_reason": "permission-denied",
        },
    ]


def test_user_port_file_validation_uses_uid_derived_port(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """User-port validation computes the expected port and stores safe evidence."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    service_file = learner_home / "site.service"
    service_file.write_text("ExecStart=/usr/bin/python3 -m http.server 14242\n", encoding="utf-8")

    with connect_database(migrated_database_path) as database_connection:
        passed_result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                UserPortFileValidation(
                    path="site.service",
                    required_regex_template=r"http\.server {port}",
                ),
                learner_home,
            ),
        )
        service_file.write_text(
            "ExecStart=/usr/bin/python3 -m http.server 9999\n",
            encoding="utf-8",
        )
        failed_result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                UserPortFileValidation(
                    path="site.service",
                    required_regex_template=r"http\.server {port}",
                ),
                learner_home,
            ),
        )

    assert passed_result.passed is True
    assert passed_result.failure_reason is None
    assert passed_result.evidence == {
        "byte_count": 48,
        "catalog_path": "site.service",
        "computed_port": 14242,
        "failure_reason": None,
        "forbidden_matched": None,
        "passed": True,
        "path_category": "learner-relative",
        "port_formula": "10000+uid",
        "required_matched": True,
        "validation_type": "user_port_file",
    }
    assert failed_result.passed is False
    assert failed_result.failure_reason == "port-content-mismatch"
    assert failed_result.evidence == {
        "byte_count": 47,
        "catalog_path": "site.service",
        "computed_port": 14242,
        "failure_reason": "port-content-mismatch",
        "forbidden_matched": None,
        "passed": False,
        "path_category": "learner-relative",
        "port_formula": "10000+uid",
        "required_matched": False,
        "validation_type": "user_port_file",
    }


def test_user_port_file_validation_reports_unknown_user(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """User-port validation needs a Unix account before computing the port."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            QuestValidationInput(
                database_connection=database_connection,
                catalog=CATALOG,
                handle="alice",
                quest=replace(
                    CATALOG.quest("prove-shell-alive"),
                    validation=UserPortFileValidation(
                        path="site.service",
                        required_regex_template=r"http\.server {port}",
                    ),
                ),
                checked_at="2026-07-19T09:00:00Z",
                assigned_at="2026-07-19T09:00:00Z",
                account_lookup=_unknown_account_lookup,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "unknown-user"
    assert result.evidence == {
        "catalog_path": "site.service",
        "failure_reason": "unknown-user",
        "passed": False,
        "port_formula": "10000+uid",
        "validation_type": "user_port_file",
    }


def test_user_port_file_validation_reports_missing_path(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Missing service files use the shared path-resolution failure reason."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                UserPortFileValidation(
                    path="missing.service",
                    required_regex_template=r"http\.server {port}",
                ),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "missing-path"
    assert result.evidence == {
        "catalog_path": "missing.service",
        "computed_port": 14242,
        "failure_reason": "missing-path",
        "passed": False,
        "path_category": "learner-relative",
        "port_formula": "10000+uid",
        "validation_type": "user_port_file",
    }


def test_user_port_file_validation_rejects_symlink_swap_escape_before_read(
    migrated_database_path: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """User-port file checks reject descriptors swapped outside learner home."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    inside_file = learner_home / "site.service"
    inside_file.write_text("ExecStart=/usr/bin/python3 -m http.server 14242\n", encoding="utf-8")
    outside_file = tmp_path / "outside.service"
    outside_file.write_text("ExecStart=/usr/bin/python3 -m http.server 14242\n", encoding="utf-8")
    link_path = learner_home / "site-link.service"
    link_path.symlink_to(inside_file)
    original_open = validation_paths.os.open

    def open_after_symlink_swap(path: Path, flags: int) -> int:
        if path == link_path:
            link_path.unlink()
            link_path.symlink_to(outside_file)
        return original_open(path, flags)

    monkeypatch.setattr(validation_paths.os, "open", open_after_symlink_swap)

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                UserPortFileValidation(
                    path="site-link.service",
                    required_regex_template=r"http\.server {port}",
                ),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "path-escapes-scope"
    assert result.evidence == {
        "catalog_path": "site-link.service",
        "computed_port": 14242,
        "failure_reason": "path-escapes-scope",
        "passed": False,
        "path_category": "learner-relative",
        "port_formula": "10000+uid",
        "validation_type": "user_port_file",
    }


def test_user_port_file_validation_reports_runtime_invalid_regex(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Invalid formatted regexes fail defensively at runtime."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()
    service_file = learner_home / "site.service"
    service_file.write_text("ExecStart=/usr/bin/python3 -m http.server 14242\n", encoding="utf-8")

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                UserPortFileValidation(
                    path="site.service",
                    required_regex_template=r"({port}",
                ),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "invalid-regex"
    assert result.evidence == {
        "byte_count": 48,
        "catalog_path": "site.service",
        "computed_port": 14242,
        "failure_reason": "invalid-regex",
        "passed": False,
        "path_category": "learner-relative",
        "port_formula": "10000+uid",
        "validation_type": "user_port_file",
    }


def test_user_port_file_validation_rejects_unsupported_formula(
    migrated_database_path: Path,
    tmp_path: Path,
) -> None:
    """Unknown port formulas fail even though catalog validation prevents them."""
    learner_home = tmp_path / "alice"
    learner_home.mkdir()

    with connect_database(migrated_database_path) as database_connection:
        result = validate_quest(
            _filesystem_validation_input(
                database_connection,
                UserPortFileValidation(
                    path="site.service",
                    required_regex_template=r"http\.server {port}",
                    port_formula="uid",
                ),
                learner_home,
            ),
        )

    assert result.passed is False
    assert result.failure_reason == "unsupported-port-formula"
    assert result.evidence == {
        "catalog_path": "site.service",
        "failure_reason": "unsupported-port-formula",
        "passed": False,
        "port_formula": "uid",
        "validation_type": "user_port_file",
    }


def test_active_catalog_validation_rules_are_runtime_supported() -> None:
    """Every active catalog validation leaf has deterministic runtime support."""
    unsupported_by_quest: dict[str, tuple[str, ...]] = {}
    for quest in CATALOG.course.quests:
        support = validation_support(quest.validation)
        if not support.supported:
            unsupported_by_quest[quest.id] = support.unsupported_validation_types

    assert unsupported_by_quest == {}


def _validation_input(
    database_connection: sqlite3.Connection,
    quest_id: str,
    assigned_at: str = "2026-07-19T09:00:00Z",
    checked_at: str = "2026-07-19T09:00:00Z",
    answer_text: str | None = None,
) -> QuestValidationInput:
    return QuestValidationInput(
        database_connection=database_connection,
        catalog=CATALOG,
        handle="alice",
        quest=CATALOG.quest(quest_id),
        checked_at=checked_at,
        assigned_at=assigned_at,
        answer_text=answer_text,
    )


def _answer_validation_input(
    database_connection: sqlite3.Connection,
    validation: QuestValidation,
    answer_text: str | None,
    assessments: tuple[AnswerConceptAssessment, ...] = (),
) -> QuestValidationInput:
    return QuestValidationInput(
        database_connection=database_connection,
        catalog=CATALOG,
        handle="alice",
        quest=replace(CATALOG.quest("prove-shell-alive"), validation=validation),
        checked_at="2026-07-19T09:00:00Z",
        assigned_at="2026-07-19T09:00:00Z",
        answer_text=answer_text,
        answer_concept_assessments=assessments,
    )


def _interactive_validation() -> InteractiveQuestionValidation:
    return InteractiveQuestionValidation(
        question="What do host and port identify?",
        required_concepts=(
            AnswerConcept(
                id="host",
                aliases=(r"\bhost\b", r"\bhostname\b"),
                rubric="Answer identifies the host.",
                forbidden_patterns=(r"\bdid\s+not\s+use\s+hostname\b",),
            ),
            AnswerConcept(
                id="port",
                aliases=(r"\bport\b",),
                rubric="Answer identifies the port.",
            ),
        ),
    )


def _filesystem_validation_input(
    database_connection: sqlite3.Connection,
    validation: QuestValidation,
    learner_home: Path,
    user_id: int | None = None,
    answer_text: str | None = None,
) -> QuestValidationInput:
    return QuestValidationInput(
        database_connection=database_connection,
        catalog=CATALOG,
        handle="alice",
        quest=replace(CATALOG.quest("prove-shell-alive"), validation=validation),
        checked_at="2026-07-19T09:00:00Z",
        assigned_at="2026-07-19T09:00:00Z",
        answer_text=answer_text,
        account_lookup=_account_lookup(learner_home, user_id),
    )


def _account_lookup(learner_home: Path, user_id: int | None = None) -> UnixAccountLookup:
    def lookup(handle: str) -> UnixAccount | None:
        if handle != "alice":
            return None
        return UnixAccount(
            handle=handle,
            user_id=4242 if user_id is None else user_id,
            home_directory=learner_home,
        )

    return lookup


def _unknown_account_lookup(handle: str) -> UnixAccount | None:
    if handle != "alice":
        raise AssertionError(f"unexpected handle: {handle}")
    return None


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
