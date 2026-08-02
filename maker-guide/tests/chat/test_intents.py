"""Tests for pure chat intent parsing."""

from __future__ import annotations

import pytest

from maker_guide.chat.intents import answer_text, chat_intent, thank_arguments


@pytest.mark.parametrize(
    ("text", "expected_intent"),
    [
        ("help", "help"),
        ("progress", "progress"),
        ("now", "now"),
        ("next", "now"),
        ("today", "now"),
        (" what should I do today ", "now"),
        ("what should I do now", "now"),
        ("check my work", "check"),
        ("am I done", "check"),
        ("answer", "answer"),
        ("answer 42", "answer"),
        ("thank bob Explained SSH permissions", "thank"),
        ("explain the quest", "freeform"),
    ],
)
def test_chat_intent_normalizes_known_phrases(text: str, expected_intent: str) -> None:
    """Known learner phrases resolve to deterministic chat intents."""
    assert chat_intent(text) == expected_intent


@pytest.mark.parametrize(
    ("text", "expected_answer"),
    [
        ("answer", None),
        (" answer   ", None),
        ("answer   because permissions changed", "because permissions changed"),
        ("hello", None),
    ],
)
def test_answer_text_extracts_answer_payload(
    text: str,
    expected_answer: str | None,
) -> None:
    """Answer payload extraction preserves only text after the answer command."""
    assert answer_text(text) == expected_answer


@pytest.mark.parametrize(
    ("text", "expected_arguments"),
    [
        ("thank bob Explained SSH permissions", ("bob", "Explained SSH permissions")),
        ("thank bob", None),
        ("thank", None),
    ],
)
def test_thank_arguments_require_recipient_and_reason(
    text: str,
    expected_arguments: tuple[str, str] | None,
) -> None:
    """Thank parsing retains the recipient and the entire required reason."""
    assert thank_arguments(text) == expected_arguments
