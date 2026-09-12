"""Learner-facing chat response formatting."""

from __future__ import annotations

from typing import cast

from maker_guide.chat.contract import ChatError
from maker_guide.chat.doc_selection import learner_document_path
from maker_guide.curriculum.models import CourseCatalog, Quest
from maker_guide.curriculum.tiers import current_tier_id
from maker_guide.progress.feedback import failure_explanation, site_check_feedback
from maker_guide.progress.models import QuestCompletionResult
from maker_guide.progress.validation import QuestValidationResult, validation_answer_question
from maker_guide.repositories.tier_promotion import TierPromotion


def format_today_quest(quest: Quest) -> str:
    """Format the deterministic current quest assignment."""
    response_parts = [
        f"Today's quest: {quest.title}",
        f"Goal:\n{quest.learner_goal}",
        f"Task:\n{quest.prompt}",
    ]
    if quest.docs:
        response_parts.append(
            "Optional reference:\n"
            + "\n".join(
                "\n".join(
                    (
                        f"- {reference.title}",
                        f"  Open: glow -p {learner_document_path(reference.path)}",
                    ),
                )
                for reference in quest.docs
            ),
        )
    if quest.hints:
        response_parts.append(f"Hint:\n{quest.hints[0].text}")
    if (question := validation_answer_question(quest.validation)) is not None:
        response_parts.append(f"Question:\n{question}")
        response_parts.append("When ready, run: guide answer 'your answer'")
    else:
        response_parts.append("When ready, run: guide check")
    return "\n\n".join(response_parts)


def format_completed_quest(
    catalog: CourseCatalog,
    quest: Quest,
    completion_result: QuestCompletionResult,
    *,
    include_next_instruction: bool = True,
) -> str:
    """Format a successful quest completion response."""
    if completion_result.completion.quest_id != quest.id:
        raise ChatError("quest completion does not match current quest")
    response_parts = [
        "Done.",
        f"Completed quest: {quest.title}",
        f"Score: {completion_result.score_total}",
        f"Tier: {current_tier_id(catalog, completion_result.score_total) or 'none'}",
    ]
    if completion_result.tier_promotions:
        response_parts.append(
            "New tier: "
            + ", ".join(
                catalog.tier(promotion.tier_id).title
                for promotion in completion_result.tier_promotions
            ),
        )
    if include_next_instruction:
        response_parts.append("Next: guide now")
    return "\n\n".join(response_parts)


def format_tier_promotion_announcements(
    promotions: tuple[TierPromotion, ...],
) -> tuple[str, ...]:
    """Format syllabus-required public IRC promotion notices."""
    announcements: list[str] = []
    for promotion in promotions:
        match promotion.tier_id:
            case "apprentice":
                announcements.append(f"{promotion.handle} became an apprentice")
            case "builder":
                announcements.append(f"{promotion.handle}: builder tier unlocked")
            case "maker":
                announcements.append(f"{promotion.handle} earned maker status")
            case _:
                raise ChatError(f"no public announcement for tier: {promotion.tier_id}")
    return tuple(announcements)


def format_failed_check(
    quest: Quest,
    validation_result: QuestValidationResult,
    tutor_feedback: str | None = None,
) -> str:
    """Format deterministic validation failure feedback."""
    explanation = failure_explanation(quest, validation_result.failure_reason)
    response_parts = [
        f"Not yet.\n\nQuest: {quest.title}",
        _found_text(explanation.found, validation_result),
    ]
    if tutor_feedback is not None:
        response_parts.append(f"Let's work through your answer:\n{tutor_feedback}")
    elif quest.docs:
        response_parts.append(f"Reference: glow -p {learner_document_path(quest.docs[0].path)}")
    return "\n\n".join(response_parts)


def _found_text(fallback_text: str, validation_result: QuestValidationResult) -> str:
    if (feedback := site_check_feedback(validation_result)) is not None:
        return feedback
    if validation_result.failure_reason != "missing-command":
        return fallback_text
    matched_commands = _string_list_evidence(validation_result, "matched_commands")
    missing_commands = _string_list_evidence(validation_result, "missing_commands")
    if not matched_commands and not missing_commands:
        return fallback_text
    return "\n".join(
        (
            fallback_text,
            f"Seen: {_command_list(matched_commands)}",
            f"Missing: {_command_list(missing_commands)}",
        ),
    )


def _string_list_evidence(validation_result: QuestValidationResult, key: str) -> tuple[str, ...]:
    value = validation_result.evidence.get(key)
    if not isinstance(value, list):
        return ()
    return tuple(item for item in cast("list[object]", value) if isinstance(item, str))


def _command_list(commands: tuple[str, ...]) -> str:
    return ", ".join(f"`{command}`" for command in commands) if commands else "none"
