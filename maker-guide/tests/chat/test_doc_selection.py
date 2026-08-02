"""Tests for deterministic tutor documentation selection."""

from __future__ import annotations

import pytest

from maker_guide.chat.doc_selection import (
    TutorDocSelectionInput,
    learner_document_path,
    select_tutor_docs,
)
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG


def test_learner_document_path_strips_package_content_prefix() -> None:
    """Learner doc paths omit the package-internal content directory."""
    assert (
        learner_document_path("content/lf2607/quests/prove-shell-alive.md")
        == "/docs/quests/prove-shell-alive.md"
    )


def test_select_tutor_docs_includes_current_quest_session_commands_and_concepts() -> None:
    """Current-state docs are selected without relying on LLM retrieval."""
    docs = select_tutor_docs(
        TutorDocSelectionInput(
            catalog=CATALOG,
            current_session_id="S1",
            pending_quests=("prove-shell-alive",),
            message="how do I start?",
        ),
    )
    learner_paths = {doc.learner_path for doc in docs}

    assert "/docs/quests/prove-shell-alive.md" in learner_paths
    assert "/docs/sessions/S01/self-study.md" in learner_paths
    assert "/docs/sessions/S01/recap.md" in learner_paths
    assert "/docs/commands/whoami.md" in learner_paths
    assert "/docs/concepts/shell-basics.md" in learner_paths
    assert docs[0].content.startswith("# Prove the shell is alive")


def test_select_tutor_docs_uses_message_mentions_and_deduplicates() -> None:
    """Learner text can pull in matching command, concept, and guide docs once."""
    docs = select_tutor_docs(
        TutorDocSelectionInput(
            catalog=CATALOG,
            current_session_id="S1",
            pending_quests=("prove-shell-alive",),
            message="ssh help for my service port and shell-basics, where is the docs index?",
        ),
    )
    learner_paths = [doc.learner_path for doc in docs]

    assert "/docs/commands/ssh.md" in learner_paths
    assert "/docs/concepts/shell-basics.md" in learner_paths
    assert "/docs/guides/docs-map.md" in learner_paths
    assert "/docs/guides/platform-reference.md" in learner_paths
    assert len(learner_paths) == len(set(learner_paths))


def test_select_tutor_docs_maps_command_forms_to_cards() -> None:
    """Shell syntax and command options resolve to their shared command cards."""
    docs = select_tutor_docs(
        TutorDocSelectionInput(
            catalog=CATALOG,
            current_session_id=None,
            pending_quests=("keep-pipeline-copy", "read-permissions"),
            message="",
        ),
    )
    learner_paths = {doc.learner_path for doc in docs}

    assert "/docs/commands/tee.md" in learner_paths
    assert "/docs/commands/ls-l.md" in learner_paths


@pytest.mark.parametrize(
    ("message", "learner_path", "expected_selected"),
    [
        ("How does tmux work?", "/docs/commands/tmux.md", True),
        ("How does grep work?", "/docs/commands/grep.md", True),
        ("What is a process?", "/docs/concepts/process.md", True),
        ("What is terminal multiplexing?", "/docs/concepts/terminal-multiplexing.md", True),
        ("What is terminal-multiplexing?", "/docs/concepts/terminal-multiplexing.md", True),
        ("How does `for` work?", "/docs/commands/for.md", True),
        ("How does a for loop work?", "/docs/commands/for.md", True),
        ("What does `for item in one two` do?", "/docs/commands/for.md", True),
        ("How does the if command work?", "/docs/commands/if.md", True),
        ("How does the read command work?", "/docs/commands/read.md", True),
        ("How does I/O work?", "/docs/concepts/io.md", True),
        ("I already tried it", "/docs/commands/read.md", False),
        ("different approach for this question", "/docs/commands/diff.md", False),
        ("different approach for this question", "/docs/commands/for.md", False),
        ("different approach for this question", "/docs/commands/if.md", False),
        ("different approach for this question", "/docs/concepts/io.md", False),
        ("what if it fails?", "/docs/commands/if.md", False),
        ("I read the error", "/docs/commands/read.md", False),
        ("Please read the docs", "/docs/commands/read.md", False),
    ],
)
def test_select_tutor_docs_matches_only_explicit_topics(
    message: str,
    learner_path: str,
    expected_selected: bool,
) -> None:
    """Topic names and aliases match without ordinary-prose false positives."""
    learner_paths = {
        document.learner_path
        for document in select_tutor_docs(
            TutorDocSelectionInput(
                catalog=CATALOG,
                current_session_id="S1",
                pending_quests=(),
                message=message,
            ),
        )
    }

    assert (learner_path in learner_paths) is expected_selected
