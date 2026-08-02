"""Tests for the Linux Foundations July 2026 catalog."""

from __future__ import annotations

import os
import re
import shutil
import sqlite3
import subprocess
from datetime import UTC, date, datetime
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import cast

from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.curriculum.documentation import command_card_slug
from maker_guide.curriculum.linux_foundations_2026_07 import (
    COURSE_ID,
    LINUX_FOUNDATIONS_2026_07,
)
from maker_guide.curriculum.models import (
    AllOfValidation,
    CommandHistoryValidation,
    FileCheckValidation,
    FileMatchesPathValidation,
    InteractiveQuestionValidation,
    IrcChannelJoinObservedValidation,
    IrcCtcpVersionValidation,
    OwnedPathValidation,
    PathExistsValidation,
    SshPublicKeyObservedValidation,
    UserPortFileValidation,
    validate_courses,
)

MARKDOWN_LINK_PATTERN = re.compile(
    r"(?<!!)\[(?P<label>[^\[\]\n]+)\]\((?P<target>[^)]+)\)",
)
RELATED_READING_LINK_PATTERN = re.compile(r"^- \[[^\]]+\]\((?P<target>[^)]+)\)$")
DOCS_PATH_PREFIX = "/docs/"


def test_linux_foundations_catalog_is_valid() -> None:
    """The production Linux Foundations catalog passes semantic validation."""
    validate_courses((LINUX_FOUNDATIONS_2026_07,))


def test_sessions_expose_independent_objective_validators() -> None:
    """Objective gates own validators instead of borrowing quest definitions."""
    objective_validation_types_by_session = {
        session.id: tuple(type(objective.validation) for objective in session.objectives)
        for session in LINUX_FOUNDATIONS_2026_07.sessions
    }

    assert objective_validation_types_by_session == {
        "S1": (
            IrcChannelJoinObservedValidation,
            CommandHistoryValidation,
            CommandHistoryValidation,
            CommandHistoryValidation,
            AllOfValidation,
        ),
        "S2": (SshPublicKeyObservedValidation,),
        "S3": (
            AllOfValidation,
            AllOfValidation,
            AllOfValidation,
            AllOfValidation,
            AllOfValidation,
            AllOfValidation,
            AllOfValidation,
            AllOfValidation,
            AllOfValidation,
            AllOfValidation,
        ),
        "S4": (
            CommandHistoryValidation,
            CommandHistoryValidation,
            PathExistsValidation,
            CommandHistoryValidation,
        ),
        "S5": (
            AllOfValidation,
            FileCheckValidation,
            FileCheckValidation,
            FileCheckValidation,
        ),
        "S6": (
            FileCheckValidation,
            FileCheckValidation,
            CommandHistoryValidation,
            CommandHistoryValidation,
        ),
        "S7": (
            CommandHistoryValidation,
            CommandHistoryValidation,
            CommandHistoryValidation,
            AllOfValidation,
        ),
        "S8": (
            CommandHistoryValidation,
            CommandHistoryValidation,
            AllOfValidation,
            AllOfValidation,
            CommandHistoryValidation,
        ),
        "S9": (
            AllOfValidation,
            CommandHistoryValidation,
            CommandHistoryValidation,
            FileCheckValidation,
            FileCheckValidation,
            AllOfValidation,
        ),
        "S10": (),
    }
    assert all(
        not hasattr(objective, "quest_id")
        for session in LINUX_FOUNDATIONS_2026_07.sessions
        for objective in session.objectives
    )


def test_catalog_exposes_course_identity_and_tiers() -> None:
    """Course ids and tiers line up with repository state ids."""
    assert LINUX_FOUNDATIONS_2026_07.id == COURSE_ID
    assert LINUX_FOUNDATIONS_2026_07.timezone == "Asia/Singapore"
    assert "Linux expert" in LINUX_FOUNDATIONS_2026_07.tutor_system_prompt
    assert "Socratic method" in LINUX_FOUNDATIONS_2026_07.tutor_system_prompt
    assert "provided learner snapshot" in LINUX_FOUNDATIONS_2026_07.tutor_system_prompt
    assert [(tier.id, tier.minimum_score) for tier in LINUX_FOUNDATIONS_2026_07.tiers] == [
        ("newcomer", 0),
        ("apprentice", 500),
        ("builder", 1000),
        ("maker", 2000),
    ]


def test_catalog_exposes_july_18_session_schedule() -> None:
    """Sessions keep explicit dates for the live course schedule."""
    assert LINUX_FOUNDATIONS_2026_07.starts_on == date(2026, 7, 18)
    assert LINUX_FOUNDATIONS_2026_07.ends_on == date(2026, 10, 24)
    assert [(session.id, session.date) for session in LINUX_FOUNDATIONS_2026_07.sessions] == [
        ("S1", date(2026, 7, 18)),
        ("S2", date(2026, 7, 25)),
        ("S3", date(2026, 8, 1)),
        ("S4", date(2026, 8, 8)),
        ("S5", date(2026, 8, 22)),
        ("S6", date(2026, 8, 29)),
        ("S7", date(2026, 9, 12)),
        ("S8", date(2026, 9, 26)),
        ("S9", date(2026, 10, 10)),
        ("S10", date(2026, 10, 24)),
    ]
    assert [(session.id, session.starts_at) for session in LINUX_FOUNDATIONS_2026_07.sessions] == [
        ("S1", datetime(2026, 7, 18, 9, tzinfo=UTC)),
        ("S2", datetime(2026, 7, 25, 9, tzinfo=UTC)),
        ("S3", datetime(2026, 8, 1, 9, tzinfo=UTC)),
        ("S4", datetime(2026, 8, 8, 9, tzinfo=UTC)),
        ("S5", datetime(2026, 8, 22, 9, tzinfo=UTC)),
        ("S6", datetime(2026, 8, 29, 9, tzinfo=UTC)),
        ("S7", datetime(2026, 9, 12, 9, tzinfo=UTC)),
        ("S8", datetime(2026, 9, 26, 9, tzinfo=UTC)),
        ("S9", datetime(2026, 10, 10, 9, tzinfo=UTC)),
        ("S10", datetime(2026, 10, 24, 9, tzinfo=UTC)),
    ]


def test_catalog_exposes_taught_commands_and_skills_by_session() -> None:
    """Lookup helpers return deterministic teaching gates."""
    assert "ssh" in CATALOG.commands_available_through("S1")
    assert "bat" in CATALOG.commands_available_through("S1")
    assert "touch" in CATALOG.commands_available_through("S2")
    assert "Get-Content" in CATALOG.commands_available_through("S2")
    assert "grep" not in CATALOG.commands_available_through("S2")
    assert "2>>" not in CATALOG.commands_available_through("S10")
    assert "uniq" in CATALOG.commands_available_through("S3")
    assert "pipes" in CATALOG.skills_available_through("S3")
    assert "text-search" in CATALOG.skills_available_through("S3")
    assert "regular-expression" not in CATALOG.skills_available_through("S8")
    assert "regular-expression" in CATALOG.skills_available_through("S9")
    assert "devices" not in CATALOG.all_skills_available_through("S10")
    assert "tmux" not in CATALOG.commands_available_through("S7")
    assert "tmux" in CATALOG.commands_available_through("S8")
    assert "terminal-multiplexing" not in CATALOG.skills_available_through("S7")
    assert "terminal-multiplexing" in CATALOG.skills_available_through("S8")
    assert "systemd-user-services" not in CATALOG.skills_available_through("S3")
    assert "kernel" not in CATALOG.skills_available_through("S1")
    assert "kernel" in CATALOG.enrichment_skills_available_through("S1")
    assert "kernel" in CATALOG.all_skills_available_through("S1")


def test_catalog_exposes_ordered_quest_lookup() -> None:
    """Quest helpers use sequence order for deterministic selection."""
    assert [quest.id for quest in CATALOG.quests_available_after("S1")] == [
        "prove-shell-alive",
        "name-system",
        "count-home-entries",
        "explain-ls",
        "read-file-ends",
    ]
    assert [quest.id for quest in CATALOG.quests_available_after("S2")] == [
        "build-playground",
        "edit-with-micro",
        "redirect-and-append",
        "copy-and-inspect-ownership",
        "personalize-homepage",
    ]
    assert [quest.id for quest in CATALOG.quests_available_after("S3")] == [
        "count-stream",
        "keep-pipeline-copy",
    ]
    assert CATALOG.quests_available_after("S8")[0].id == "keep-tmux-workbench"
    assert [quest.id for quest in CATALOG.quests_available_through("S2")] == [
        "prove-shell-alive",
        "name-system",
        "count-home-entries",
        "explain-ls",
        "read-file-ends",
        "build-playground",
        "edit-with-micro",
        "redirect-and-append",
        "copy-and-inspect-ownership",
        "personalize-homepage",
    ]
    assert CATALOG.next_quest_after(None, "S1") == CATALOG.quest("prove-shell-alive")
    assert CATALOG.next_quest_after("prove-shell-alive", "S1") == CATALOG.quest("name-system")
    assert CATALOG.next_quest_after("explain-ls", "S1") == CATALOG.quest("read-file-ends")
    assert CATALOG.next_quest_after("copy-and-inspect-ownership", "S2") == CATALOG.quest(
        "personalize-homepage",
    )
    assert CATALOG.next_quest_after("personalize-homepage", "S2") is None
    assert CATALOG.next_quest_after("write-next-path", "S9") == CATALOG.quest(
        "prepare-source-handoff",
    )
    assert CATALOG.next_quest_after("prepare-source-handoff", "S9") == CATALOG.quest(
        "use-terminal-irc",
    )
    assert CATALOG.next_quest_after("use-terminal-irc", "S9") is None
    assert CATALOG.next_assignable_quest("S1", frozenset()) == CATALOG.quest("prove-shell-alive")
    assert CATALOG.next_assignable_quest(
        "S1",
        frozenset(
            {
                "prove-shell-alive",
                "name-system",
                "count-home-entries",
                "explain-ls",
            },
        ),
    ) == CATALOG.quest("read-file-ends")
    assert CATALOG.next_assignable_quest("S2", frozenset()) == CATALOG.quest(
        "build-playground",
    )
    assert CATALOG.next_assignable_quest(
        "S2",
        frozenset(
            {
                "prove-shell-alive",
                "name-system",
                "count-home-entries",
                "explain-ls",
                "read-file-ends",
                "build-playground",
                "edit-with-micro",
                "redirect-and-append",
                "copy-and-inspect-ownership",
            },
        ),
    ) == CATALOG.quest("personalize-homepage")
    assert CATALOG.next_assignable_quest(
        "S2",
        frozenset(quest.id for quest in CATALOG.quests_available_after("S2")),
    ) == CATALOG.quest("prove-shell-alive")
    assert [
        quest.id
        for quest in CATALOG.prioritized_quests(
            "S2",
            CATALOG.quests_available_through("S2"),
        )
    ] == [
        "build-playground",
        "edit-with-micro",
        "redirect-and-append",
        "copy-and-inspect-ownership",
        "personalize-homepage",
        "prove-shell-alive",
        "name-system",
        "count-home-entries",
        "explain-ls",
        "read-file-ends",
    ]


def test_prove_shell_alive_requires_explicit_guide_check() -> None:
    """Both quest surfaces distinguish command evidence from completion."""
    expected_instruction = "The commands provide evidence. Run `guide check` to complete the quest."
    quest_document = _content_text(f"content/{COURSE_ID}/quests/prove-shell-alive.md")

    assert expected_instruction in CATALOG.quest("prove-shell-alive").autonomy_checklist
    assert expected_instruction in quest_document
    assert "Progress records automatically" not in quest_document


def test_s2_quests_use_file_and_identity_validation() -> None:
    """S2 exercises cover file checks and ownership proof checks."""
    assert isinstance(CATALOG.quest("build-playground").validation, PathExistsValidation)
    assert isinstance(CATALOG.quest("edit-with-micro").validation, FileCheckValidation)
    assert isinstance(CATALOG.quest("redirect-and-append").validation, FileCheckValidation)
    ownership_validation = CATALOG.quest("copy-and-inspect-ownership").validation
    assert isinstance(ownership_validation, AllOfValidation)
    assert isinstance(ownership_validation.validations[0], OwnedPathValidation)
    assert isinstance(ownership_validation.validations[1], FileMatchesPathValidation)
    homepage_validation = CATALOG.quest("personalize-homepage").validation
    assert isinstance(homepage_validation, AllOfValidation)
    assert {
        validation.path
        for validation in homepage_validation.validations
        if isinstance(validation, FileCheckValidation)
        and validation.forbidden_regex == r"A Linux site under construction"
    } == {"~/src/pages/index.md", "~/public_html/index.html"}
    assert CATALOG.session("S2").objectives[0].id == "ssh-public-key"


def test_s1_site_build_is_not_repeated_as_a_quest() -> None:
    """The first site build is a live objective, not a reinforcement quest."""
    assert "build-first-site" not in {quest.id for quest in CATALOG.course.quests}
    assert all(
        "build-website" not in quest.required_commands
        for quest in CATALOG.quests_available_after("S1")
    )


def test_s7_setup_page_requires_linked_rebuild_evidence() -> None:
    """The setup-page quest checks source, index link, output, and build command."""
    setup_validation = CATALOG.quest("create-setup-page").validation

    assert isinstance(setup_validation, AllOfValidation)
    assert any(
        isinstance(validation, FileCheckValidation)
        and validation.path == "~/src/pages/setup.md"
        and "#" in validation.required_regex
        for validation in setup_validation.validations
    )
    assert any(
        isinstance(validation, FileCheckValidation)
        and validation.path == "~/src/pages/index.md"
        and "setup" in validation.required_regex
        for validation in setup_validation.validations
    )
    assert any(
        isinstance(validation, CommandHistoryValidation)
        and r"^(?:build-website|maker-guide-build-personal-website)$"
        in validation.required_patterns
        for validation in setup_validation.validations
    )


def test_s3_objectives_and_reinforcement_require_lesson_evidence() -> None:
    """S3 checks cover streams, useful pipelines, and processes."""
    objectives = {objective.id: objective for objective in CATALOG.session("S3").objectives}
    combined_stream_validation = objectives["combine-and-copy-streams"].validation
    stream_validation = objectives["separate-standard-streams"].validation
    process_validation = objectives["read-process-table"].validation
    count_stream_validation = CATALOG.quest("count-stream").validation
    pipeline_copy_validation = CATALOG.quest("keep-pipeline-copy").validation

    assert isinstance(combined_stream_validation, AllOfValidation)
    assert any(
        isinstance(validation, CommandHistoryValidation)
        and validation.required_patterns
        == (r"^date --debug \+%F 2>&1\s*\|\s*tee ~/playground/combined\.txt\s*\|\s*wc -l$",)
        and validation.observed_commands
        == ("date --debug +%F 2>&1 | tee ~/playground/combined.txt | wc -l",)
        for validation in combined_stream_validation.validations
    )
    assert any(
        isinstance(validation, FileCheckValidation)
        and validation.path == "~/playground/combined.txt"
        and validation.required_regex
        == (
            r"(?ms)(?=.*^date:[^\n]*%F[^\n]*$)"
            r"(?=.*^[0-9]{4}-[0-9]{2}-[0-9]{2}$).+"
        )
        for validation in combined_stream_validation.validations
    )
    assert isinstance(stream_validation, AllOfValidation)
    stream_file_checks = {
        validation.path: validation
        for validation in stream_validation.validations
        if isinstance(validation, FileCheckValidation)
    }
    assert set(stream_file_checks) == {"~/playground/stdout.txt", "~/playground/stderr.txt"}
    assert stream_file_checks["~/playground/stdout.txt"].required_regex == r"(?m)^/etc/hostname$"
    assert stream_file_checks["~/playground/stdout.txt"].forbidden_regex == r"no/such/path"
    assert stream_file_checks["~/playground/stderr.txt"].required_regex == r"no/such/path"
    assert stream_file_checks["~/playground/stderr.txt"].forbidden_regex == r"/etc/hostname"
    assert any(
        isinstance(validation, CommandHistoryValidation)
        and validation.required_patterns == (r"^cat /etc/hostname\s*>\s*/dev/null$",)
        and validation.observed_commands == ("cat /etc/hostname > /dev/null",)
        for validation in stream_validation.validations
    )
    assert all(
        not any("no/such/path" in pattern for pattern in validation.required_patterns)
        for validation in stream_validation.validations
        if isinstance(validation, CommandHistoryValidation)
    )
    assert objectives["separate-standard-streams"].prompt.count("mkdir -p ~/playground") == 1
    assert tuple(objectives) == (
        "separate-standard-streams",
        "make-first-pipe",
        "name-stdout-descriptor",
        "name-stdin-descriptor",
        "combine-and-copy-streams",
        "read-redirections-left-to-right",
        "route-stderr-to-stdout-destination",
        "read-process-table",
        "describe-running-process",
        "report-process-pair",
    )
    interactive_validations = tuple(
        validation
        for objective in objectives.values()
        if isinstance(objective.validation, AllOfValidation)
        for validation in objective.validation.validations
        if isinstance(validation, InteractiveQuestionValidation)
    )
    assert len(interactive_validations) == 9
    assert all(len(validation.required_concepts) == 1 for validation in interactive_validations)
    for objective_id in (
        "make-first-pipe",
        "name-stdout-descriptor",
        "name-stdin-descriptor",
    ):
        objective_validation = objectives[objective_id].validation
        assert isinstance(objective_validation, AllOfValidation)
        assert any(
            isinstance(validation, CommandHistoryValidation)
            and validation.required_patterns == (r"^cut -d: -f1 /etc/passwd\s*\|\s*wc -l$",)
            for validation in objective_validation.validations
        )
    for objective_id in (
        "combine-and-copy-streams",
        "read-redirections-left-to-right",
        "route-stderr-to-stdout-destination",
    ):
        objective_validation = objectives[objective_id].validation
        assert isinstance(objective_validation, AllOfValidation)
        assert any(
            isinstance(validation, FileCheckValidation)
            and validation.path == "~/playground/combined.txt"
            for validation in objective_validation.validations
        )
    for objective_id in (
        "read-process-table",
        "describe-running-process",
        "report-process-pair",
    ):
        objective_validation = objectives[objective_id].validation
        assert isinstance(objective_validation, AllOfValidation)
        assert any(
            isinstance(validation, CommandHistoryValidation)
            and validation.required_patterns == (r'^ps -u "\$USER" -o pid,comm,args$',)
            for validation in objective_validation.validations
        )
    assert isinstance(process_validation, AllOfValidation)
    assert any(
        isinstance(validation, CommandHistoryValidation)
        and validation.required_patterns == (r'^ps -u "\$USER" -o pid,comm,args$',)
        for validation in process_validation.validations
    )
    assert isinstance(count_stream_validation, CommandHistoryValidation)
    assert count_stream_validation.required_patterns == (
        r"^cut -d: -f7 /etc/passwd\s*\|\s*sort -u\s*\|\s*wc -l$",
    )
    assert isinstance(pipeline_copy_validation, AllOfValidation)
    assert any(
        isinstance(validation, FileCheckValidation)
        and validation.path == "~/playground/login-shells.txt"
        for validation in pipeline_copy_validation.validations
    )
    assert (
        "report one labeled numeric PID and command pair you read"
        in objectives["report-process-pair"].prompt
    )


def test_s3_combined_stream_pipeline_succeeds_with_pipefail(
    temporary_path: Path,
) -> None:
    """The documented GNU date pipeline preserves both streams and exits zero."""
    combined_output_path = temporary_path / "playground" / "combined.txt"
    combined_output_path.parent.mkdir()
    documented_pipeline = "date --debug +%F 2>&1 | tee ~/playground/combined.txt | wc -l"
    bash_path = shutil.which("bash")
    assert bash_path is not None

    completed_process = subprocess.run(
        [
            bash_path,
            "--noprofile",
            "--norc",
            "-c",
            f"set -o pipefail\n{documented_pipeline}",
        ],
        check=False,
        capture_output=True,
        env=os.environ | {"HOME": str(temporary_path)},
        text=True,
    )
    combined_output = combined_output_path.read_text(encoding="utf-8")

    assert completed_process.returncode == 0, completed_process.stderr
    assert completed_process.stdout.strip() == "2"
    assert len(combined_output.splitlines()) == 2
    assert re.search(r"(?m)^date:[^\n]*%F[^\n]*$", combined_output)
    assert re.search(r"(?m)^[0-9]{4}-[0-9]{2}-[0-9]{2}$", combined_output)


def test_open_concept_index_preserves_authored_skill_ownership() -> None:
    """The complete index keeps S3 core, enrichment, and later regex visibly distinct."""
    concept_index = _content_text(f"content/{COURSE_ID}/concepts/README.md")

    assert concept_index.index("(text-search.md)") < concept_index.index("### Go Deeper After S03")
    assert concept_index.index("### Go Deeper After S03") < concept_index.index("(signal.md)")
    assert concept_index.index("## S09 Polish") < concept_index.index("(regular-expression.md)")


def test_s3_cards_keep_later_syntax_out_of_completion_criteria() -> None:
    """Open cards identify read-ahead syntax without expanding the S3 proof scope."""
    stream_redirection = _content_text(f"content/{COURSE_ID}/concepts/stream-redirection.md")

    assert "`2>>` is optional exploration for later" in stream_redirection
    assert (
        "`2>>`"
        not in stream_redirection.split("## Done When", maxsplit=1)[1].split(
            "## Go Deeper", maxsplit=1
        )[0]
    )
    assert "Regex anchors are optional exploration for later" in _content_text(
        f"content/{COURSE_ID}/commands/grep.md"
    )
    assert "`2>>` is optional exploration for later" in _content_text(
        f"content/{COURSE_ID}/commands/stderr-redirect.md"
    )


def test_s3_guide_answer_commands_quote_shell_payloads() -> None:
    """Every S3 terminal answer example survives shell parsing as one argument."""
    answer_commands = [
        f"guide answer {answer_match.group('payload')}"
        for document_path in (
            f"content/{COURSE_ID}/README.md",
            f"content/{COURSE_ID}/guides/platform-reference.md",
            f"content/{COURSE_ID}/quests/README.md",
            *(content.path for content in CATALOG.session("S3").content),
            *(
                content.path
                for quest in CATALOG.quests_available_after("S3")
                for content in quest.docs
            ),
        )
        for answer_match in re.finditer(
            r"`guide answer (?P<payload>[^`]+)`",
            _content_text(document_path),
        )
    ]

    assert len(answer_commands) == 8
    bash_path = shutil.which("bash")
    assert bash_path is not None
    for answer_command in answer_commands:
        assert answer_command.startswith("guide answer '")
        assert answer_command.endswith("'")
        completed_process = subprocess.run(
            [
                bash_path,
                "--noprofile",
                "--norc",
                "-c",
                f"set -- {answer_command}\nprintf '%s\\0' \"$@\"",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed_process.returncode == 0, completed_process.stderr
        assert completed_process.stdout.split("\0") == [
            "guide",
            "answer",
            answer_command.removeprefix("guide answer '").removesuffix("'"),
            "",
        ]


def test_s3_material_uses_one_quick_preflight_and_does_not_supply_answers() -> None:
    """S3 restores its work directory once and asks learners to explain concepts themselves."""
    session_documents = tuple(
        _content_text(content.path) for content in CATALOG.session("S3").content
    )
    session_text = "\n".join(session_documents)
    objectives = {objective.id: objective for objective in CATALOG.session("S3").objectives}
    pipe_objective = objectives["make-first-pipe"]

    assert all(document.count("mkdir -p ~/playground") == 1 for document in session_documents)
    assert "guide answer 'cut writes stdout (1); wc reads stdin (0)'" not in session_text
    assert (
        "guide answer 'A binary executable is a program file; a process is a running instance.'"
        not in session_text
    )
    assert "The file can exist for years." not in session_text
    assert "Bash" not in session_text
    assert "`cut` writes stdout" not in pipe_objective.prompt
    assert "`wc` reads stdin" not in pipe_objective.prompt
    assert "stdout" not in pipe_objective.title.casefold()
    assert "stdin" not in pipe_objective.title.casefold()
    assert "left to right" not in objectives["read-redirections-left-to-right"].title.casefold()
    assert "stdout" not in objectives["route-stderr-to-stdout-destination"].title.casefold()
    assert "answer payload" not in session_text


def test_curriculum_avoids_shell_redirection_as_answer_placeholder() -> None:
    """Terminal answer placeholders are quoted instead of parsed as redirections."""
    for markdown_resource in _markdown_resources(_content_root()):
        assert "guide answer <" not in markdown_resource.read_text(encoding="utf-8"), (
            f"shell-unsafe guide answer placeholder in {markdown_resource}"
        )
    assert all(
        "guide answer <" not in hint.text for quest in CATALOG.course.quests for hint in quest.hints
    )
    assert all(
        "guide answer <" not in feedback.text
        for quest in CATALOG.course.quests
        for feedback in quest.failure_feedback
    )


def test_s8_tmux_and_service_quests_require_real_evidence() -> None:
    """S8 validators require the tmux lifecycle and real service evidence."""
    objectives = {objective.id: objective for objective in CATALOG.session("S8").objectives}
    tmux_objective_validation = objectives["keep-tmux-workbench"].validation
    tmux_validation = CATALOG.quest("keep-tmux-workbench").validation
    log_validation = CATALOG.quest("watch-service-logs").validation
    manual_server_validation = CATALOG.quest("serve-local-check-page").validation
    site_service_validation = CATALOG.quest("enable-site-service").validation

    assert isinstance(tmux_objective_validation, CommandHistoryValidation)
    assert tmux_objective_validation.ordered is True
    assert tmux_objective_validation.required_patterns == (
        r"^tmux new -s workbench$",
        r"^tmux ls$",
        r"^tmux attach -t workbench$",
        r"^tmux kill-session -t workbench$",
    )
    assert isinstance(tmux_validation, CommandHistoryValidation)
    assert tmux_validation.ordered is True
    assert tmux_validation.required_patterns == (
        r"^tmux new -s quest-workbench$",
        r"^tmux ls$",
        r"^tmux attach -t quest-workbench$",
        r"^tmux kill-session -t quest-workbench$",
    )
    assert isinstance(log_validation, CommandHistoryValidation)
    assert log_validation.ordered is True
    assert log_validation.required_patterns == (
        r"^tmux new -s logs$",
        r"^curl ",
        r"^journalctl --user -u site\.service -f$",
        r"^tmux attach -t logs$",
        r"^tmux kill-session -t logs$",
    )
    assert isinstance(manual_server_validation, CommandHistoryValidation)
    assert manual_server_validation.ordered is True
    assert manual_server_validation.required_patterns == (
        r"^systemctl --user stop site\.service$",
        r"^tmux new -s local-server$",
        r"^tmux ls$",
        r"^curl ",
        r"python3 -m http\.server",
        r"^tmux attach -t local-server$",
        r"^tmux kill-session -t local-server$",
        r"^systemctl --user start site\.service$",
    )
    assert isinstance(site_service_validation, AllOfValidation)
    assert any(
        isinstance(validation, UserPortFileValidation)
        and "{port}" in validation.required_regex_template
        for validation in site_service_validation.validations
    )
    assert any(
        isinstance(validation, CommandHistoryValidation)
        and r"^systemctl --user enable --now site\.service$" in validation.required_patterns
        and r'^curl -I "?http://127\.0\.0\.1:(?:[0-9]+|\$PORT|\$\{PORT\})/"?$'
        in validation.required_patterns
        for validation in site_service_validation.validations
    )


def test_s9_automation_quests_require_cleanup_and_runtime_evidence() -> None:
    """Automation quests require more than artifact existence."""
    cron_validation = CATALOG.quest("try-cron-and-remove-it").validation
    webring_validation = CATALOG.quest("enable-webring").validation
    timer_validation = CATALOG.quest("schedule-site-rebuilds").validation

    assert isinstance(cron_validation, AllOfValidation)
    assert any(
        isinstance(validation, FileCheckValidation)
        and validation.path == "~/crontab.after"
        and validation.forbidden_regex == r"cron\.log"
        for validation in cron_validation.validations
    )
    assert any(
        isinstance(validation, CommandHistoryValidation)
        and r"^crontab -l > ~/crontab\.after 2>/dev/null \|\| true$" in validation.required_patterns
        for validation in cron_validation.validations
    )
    assert isinstance(webring_validation, AllOfValidation)
    assert any(
        isinstance(validation, FileCheckValidation)
        and "(?=.*\\bprevious\\b)" in validation.required_regex
        and "(?=.*\\bnext\\b)" in validation.required_regex
        for validation in webring_validation.validations
    )
    assert isinstance(timer_validation, AllOfValidation)
    assert any(
        isinstance(validation, FileCheckValidation)
        and validation.path == "~/.config/systemd/user/site-build.service"
        and "/usr/local/bin/npm run build" in validation.required_regex
        for validation in timer_validation.validations
    )
    assert any(
        isinstance(validation, CommandHistoryValidation)
        and r"^systemctl --user enable --now site-build\.timer$" in validation.required_patterns
        for validation in timer_validation.validations
    )


def test_s10_terminal_irc_quest_uses_ctcp_version_validation() -> None:
    """The terminal IRC challenge accepts only terminal IRC clients."""
    quest = CATALOG.quest("use-terminal-irc")
    validation = CATALOG.quest("use-terminal-irc").validation

    assert quest.required_commands == ("weechat",)
    assert isinstance(validation, IrcCtcpVersionValidation)
    assert validation.accepted_clients == ("WeeChat", "irssi", "BitchX")


def test_packaged_content_references_exist_and_are_non_empty() -> None:
    """Catalog content references point at packaged Markdown resources."""
    for content_reference in CATALOG.content_references():
        assert _content_text(content_reference.path).strip() != ""


def test_course_has_top_level_start_page() -> None:
    """Autonomous learners have a deterministic entry point."""
    start_text = _content_text(f"content/{COURSE_ID}/README.md")

    assert "Start here" in start_text
    assert "## Optional Quest Map" in start_text
    assert "## Quest Calendar" in start_text
    assert "They are not prerequisites for attending the next live session." in start_text


def test_open_reference_indexes_link_every_card() -> None:
    """Every open command and concept card is discoverable from its authored index."""
    for directory_name in ("commands", "concepts"):
        card_directory = _content_root().joinpath(directory_name)
        indexed_card_names = {
            Path(link_target.partition("#")[0]).name
            for link_target in _markdown_link_targets(
                card_directory.joinpath("README.md").read_text(encoding="utf-8")
            )
        }

        assert indexed_card_names == {
            child_resource.name
            for child_resource in card_directory.iterdir()
            if child_resource.is_file()
            and child_resource.name.endswith(".md")
            and child_resource.name != "README.md"
        }


def test_content_link_labels_close_inline_code_spans() -> None:
    """Every Markdown link label has balanced inline-code delimiters."""
    for markdown_resource in _markdown_resources(_content_root()):
        for link_match in MARKDOWN_LINK_PATTERN.finditer(
            markdown_resource.read_text(encoding="utf-8"),
        ):
            assert link_match.group("label").count("`") % 2 == 0, (
                f"unbalanced inline code in {markdown_resource}: {link_match.group()}"
            )


def test_local_markdown_links_resolve() -> None:
    """Every local Markdown link points at a packaged resource on disk."""
    for markdown_resource in _markdown_resources(_content_root()):
        for link_target in _markdown_link_targets(markdown_resource.read_text(encoding="utf-8")):
            if _is_external_or_page_anchor(link_target):
                continue
            assert _linked_resource_path(markdown_resource, link_target).exists(), (
                f"broken link in {markdown_resource}: {link_target}"
            )


def test_quest_related_reading_entries_are_clickable_links() -> None:
    """Quest reading lists must be links, not inert path text."""
    for markdown_resource in _markdown_resources(_content_root().joinpath("quests")):
        for related_reading_entry in _related_reading_entries(
            markdown_resource.read_text(encoding="utf-8"),
        ):
            assert RELATED_READING_LINK_PATTERN.fullmatch(related_reading_entry), (
                f"non-link related reading in {markdown_resource}: {related_reading_entry}"
            )


def test_quest_command_sections_match_catalog() -> None:
    """Quest command lists are rendered from catalog intent without drift."""
    for quest in LINUX_FOUNDATIONS_2026_07.quests:
        quest_text = _content_text(f"content/{COURSE_ID}/quests/{quest.id}.md")

        assert _quest_command_entries(quest_text) == quest.required_commands


def test_sessions_have_presenterm_slides_self_study_and_recaps() -> None:
    """Every live session has cataloged live and autonomous learner content."""
    for session in LINUX_FOUNDATIONS_2026_07.sessions:
        content_by_purpose = {
            content_reference.purpose: content_reference for content_reference in session.content
        }
        assert set(content_by_purpose) == {"slides", "self-study", "recap"}
        assert content_by_purpose["slides"].path.endswith(
            f"sessions/{_session_directory(session.id)}/slides.md",
        )
        assert content_by_purpose["self-study"].path.endswith(
            f"sessions/{_session_directory(session.id)}/self-study.md",
        )
        slides_text = _content_text(content_by_purpose["slides"].path)
        assert f"Session: {session.id}" in slides_text
        assert "<!-- end_slide -->" in slides_text
        assert "---" not in slides_text.splitlines()


def test_sessions_have_autonomous_self_study_guides() -> None:
    """Every session has a standalone learner guide with recovery and proof sections."""
    recovery_markers = ("## Troubleshooting", "## Git Recovery", "## Stuck Table")

    for session in LINUX_FOUNDATIONS_2026_07.sessions:
        content_by_purpose = {
            content_reference.purpose: content_reference for content_reference in session.content
        }
        self_study_text = _content_text(content_by_purpose["self-study"].path)
        assert f"Session: {session.id}" in self_study_text
        assert "## Study Path" in self_study_text
        assert any(marker in self_study_text for marker in recovery_markers)
        assert "## Proof Checklist" in self_study_text
        assert "## Docs Pointers" in self_study_text


def test_full_course_autonomous_content_covers_commands_skills_and_quests() -> None:
    """Every session has enough packaged content for autonomous learner progress."""
    for session in LINUX_FOUNDATIONS_2026_07.sessions:
        _assert_autonomous_content_through(session.id)


def test_high_friction_command_cards_have_docs_pointers() -> None:
    """Troubleshooting-heavy commands point learners to authoritative references."""
    for command in (
        "bat",
        "chmod",
        "chmod +x",
        "journalctl --user",
        "systemd timer",
        "cron",
        "crontab",
        "rm -rf",
        "set -euo pipefail",
        "sed",
        "awk",
        "vim",
    ):
        assert "## Docs Pointers" in _content_text(_command_document_path(command))


def test_git_command_index_exists() -> None:
    """The git command family has an index page for learner navigation."""
    assert _content_text(f"content/{COURSE_ID}/commands/git.md").strip() != ""


def _assert_autonomous_content_through(session_id: str) -> None:
    for command in CATALOG.commands_available_through(session_id):
        assert _content_text(_command_document_path(command)).strip() != ""

    for skill in CATALOG.all_skills_available_through(session_id):
        assert _content_text(f"content/{COURSE_ID}/concepts/{skill}.md").strip() != ""

    for quest in CATALOG.quests_available_after(session_id):
        quest_text = _content_text(f"content/{COURSE_ID}/quests/{quest.id}.md")
        assert f"Quest: {quest.id}" in quest_text
        assert "## Mission" in quest_text
        assert "## Commands You Will Use" in quest_text
        assert "## Hints" in quest_text
        assert "## If Check Fails" in quest_text
        assert len(quest.hints) >= 3
        assert quest.failure_feedback
        assert quest.story.strip() != ""
        assert quest.learner_goal.strip() != ""
        assert quest.autonomy_checklist


def test_curriculum_content_uses_current_course_hosts_and_day_language() -> None:
    """Packaged teaching content uses current domain names and daytime session language."""
    all_content_text = "\n".join(
        markdown_resource.read_text(encoding="utf-8")
        for markdown_resource in _markdown_resources(_content_root())
    )

    assert "kolammakers.cc" not in all_content_text
    assert "genesis.kolammakers.cc" not in all_content_text
    assert "$fqdn" not in all_content_text
    assert "hello kolam" not in all_content_text.lower()
    assert "tonight" not in all_content_text.lower()
    assert "learner service" not in all_content_text.lower()
    assert "learner-managed service" not in all_content_text.lower()
    assert "Allowed Commands" not in all_content_text
    assert "TheGuide" not in all_content_text
    assert "lf2607.kolamayermakers.org" in all_content_text
    assert "https://lf2607.kolamayermakers.org/git/" in all_content_text
    assert "https://lf2607.kolamayermakers.org/irc/" in all_content_text
    assert "git.kolamayermakers.org" not in all_content_text
    assert "irc.kolamayermakers.org" not in all_content_text
    assert "lf2607.kolamayermakers.org/~username" in all_content_text
    assert "ssh-copy-id <handle>@lf2607.kolamayermakers.org" in all_content_text
    assert "Get-Content ~/.ssh/id_ed25519.pub" in all_content_text
    assert "preview-only command" in all_content_text
    assert "ssh-copy-id" in all_content_text
    assert "cat >> ~/.ssh/authorized_keys" in all_content_text
    assert "chmod 700 ~/.ssh" in all_content_text
    assert "current objective or quest" not in all_content_text
    assert "current session objective" in all_content_text


def test_webring_uses_the_deployed_course_group() -> None:
    """Webring membership follows the deployed Linux Foundations group."""
    site_source = files("maker_guide.astro_starter").joinpath("template/app/lib/site.mjs")

    assert '["group", "linux-foundations"]' in site_source.read_text(encoding="utf-8")
    assert '["group", "lf2607"]' not in site_source.read_text(encoding="utf-8")


def test_curriculum_content_keeps_quests_optional_and_internals_hidden() -> None:
    """Learner content does not make quests into live-session gates or leak internals."""
    all_content_text = "\n".join(
        markdown_resource.read_text(encoding="utf-8")
        for markdown_resource in _markdown_resources(_content_root(), frozenset({"mentors"}))
    )

    for forbidden_phrase in (
        "Python catalog",
        "maker-guide",
        "validation logic",
        "Autonomous Quest Spine",
        "Run your daily quests",
        "Fix failures before the polish session",
        "before the live session starts",
        "complete quests before",
        "quests are required",
    ):
        assert forbidden_phrase not in all_content_text


def test_sqlite_schema_stores_catalog_ids_not_catalog_definitions(
    migrated_database_path: Path,
) -> None:
    """SQLite learner state stores catalog ids, not catalog-owned definition tables."""
    with sqlite3.connect(migrated_database_path) as database_connection:
        table_name_rows = cast(
            "list[tuple[str]]",
            database_connection.execute(
                "select name from sqlite_master where type = 'table'",
            ).fetchall(),
        )

    assert {"courses", "sessions", "quests", "tiers"}.isdisjoint(
        {table_name for (table_name,) in table_name_rows},
    )


def _content_root() -> Traversable:
    return files("maker_guide.curriculum").joinpath("content", COURSE_ID)


def _content_text(content_path: str) -> str:
    return files("maker_guide.curriculum").joinpath(content_path).read_text(encoding="utf-8")


def _markdown_link_targets(markdown_text: str) -> tuple[str, ...]:
    return tuple(
        _link_path_without_title(link_match.group("target"))
        for link_match in MARKDOWN_LINK_PATTERN.finditer(markdown_text)
    )


def _link_path_without_title(link_target: str) -> str:
    return link_target.split(maxsplit=1)[0]


def _is_external_or_page_anchor(link_target: str) -> bool:
    return link_target.startswith(("#", "mailto:")) or "://" in link_target


def _linked_resource_path(markdown_resource: Traversable, link_target: str) -> Path:
    link_path = link_target.split("#", maxsplit=1)[0]
    if link_path.startswith(DOCS_PATH_PREFIX):
        return (Path(str(_content_root())) / link_path.removeprefix(DOCS_PATH_PREFIX)).resolve()
    return (Path(str(markdown_resource)).parent / link_path.removeprefix("./")).resolve()


def _related_reading_entries(markdown_text: str) -> tuple[str, ...]:
    related_reading_heading = "## Related Reading"
    if related_reading_heading not in markdown_text:
        return ()
    related_reading_text = markdown_text.split(related_reading_heading, maxsplit=1)[1]
    section_text = related_reading_text.split("\n## ", maxsplit=1)[0]
    return tuple(line for line in section_text.splitlines() if line.startswith("- "))


def _quest_command_entries(markdown_text: str) -> tuple[str, ...]:
    command_heading = "## Commands You Will Use"
    if command_heading not in markdown_text:
        return ()
    command_section_text = markdown_text.split(command_heading, maxsplit=1)[1]
    section_text = command_section_text.split("\n## ", maxsplit=1)[0]
    return tuple(
        line.removeprefix("- `").removesuffix("`")
        for line in section_text.splitlines()
        if line.startswith("- `") and line.endswith("`")
    )


def _command_document_path(command: str) -> str:
    return f"content/{COURSE_ID}/commands/{command_card_slug(command)}.md"


def _session_directory(session_id: str) -> str:
    return f"S{int(session_id.removeprefix('S')):02d}"


def _markdown_resources(
    root: Traversable,
    excluded_directory_names: frozenset[str] = frozenset(),
) -> tuple[Traversable, ...]:
    markdown_resources: list[Traversable] = []
    for child in root.iterdir():
        if child.is_dir():
            if child.name not in excluded_directory_names:
                markdown_resources.extend(
                    _markdown_resources(child, excluded_directory_names),
                )
        elif child.name.endswith(".md"):
            markdown_resources.append(child)
    return tuple(markdown_resources)
