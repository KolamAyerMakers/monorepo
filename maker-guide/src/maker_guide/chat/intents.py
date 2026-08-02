"""Pure chat intent parsing."""

from __future__ import annotations

from typing import Literal

ChatIntent = Literal["help", "progress", "now", "check", "answer", "thank", "freeform"]


def chat_intent(text: str) -> ChatIntent:  # noqa: PLR0911 - Intent recognition stays direct.
    """Resolve learner text to the deterministic chat intent."""
    normalized_text = " ".join(text.casefold().strip().split())
    if normalized_text == "help":
        return "help"
    if normalized_text == "progress":
        return "progress"
    if normalized_text == "answer" or normalized_text.startswith("answer "):
        return "answer"
    if normalized_text == "thank" or normalized_text.startswith("thank "):
        return "thank"
    match normalized_text:
        case "now" | "next":
            return "now"
        case (
            "today" | "what should i do today" | "what should i do now" | "current quest" | "quest"
        ):
            return "now"
        case "check" | "check my work" | "am i finished" | "am i done" | "done":
            return "check"
        case _:
            return "freeform"


def answer_text(text: str) -> str | None:
    """Extract the free-form answer payload from answer intents."""
    stripped_text = text.strip()
    if stripped_text.casefold() == "answer":
        return None
    if not stripped_text.casefold().startswith("answer "):
        return None
    extracted_answer = stripped_text[len("answer") :].strip()
    return extracted_answer or None


def thank_arguments(text: str) -> tuple[str, str] | None:
    """Extract the recipient and required reason from a thank command."""
    command_parts = text.strip().split(maxsplit=2)
    if len(command_parts) != 3 or command_parts[0].casefold() != "thank":
        return None
    recipient_handle = command_parts[1]
    reason = command_parts[2].strip()
    if not recipient_handle or not reason:
        return None
    return recipient_handle, reason
