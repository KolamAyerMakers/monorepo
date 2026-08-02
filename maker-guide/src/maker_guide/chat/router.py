"""Chat intent routing to response drafts."""

from __future__ import annotations

from maker_guide.chat.contract import (
    ChatDependencies,
    ChatRequest,
    PreparedAnswerInterpretation,
    ResponseDraft,
)
from maker_guide.chat.intents import answer_text, chat_intent
from maker_guide.chat.presenter import format_tier_promotion_announcements
from maker_guide.chat.progress import check_response, now_response, progress_response
from maker_guide.chat.thanks import thank_response
from maker_guide.chat.tutor import freeform_response_draft, routes_bare_interactive_answer

_HELP_TEXT = (
    "In a terminal: `guide progress`, `guide now`, `guide next`, `guide check`, or "
    "`guide answer 'your answer'`. In a guide DM: `progress`, `now`, `next`, `check`, or "
    "`answer <your answer>`. Public IRC: `!help <question>` or `!thank nickname reason`."
)


def build_response_draft(  # noqa: PLR0911 - Each chat intent has one direct response path.
    request: ChatRequest,
    dependencies: ChatDependencies,
    learner_handle: str,
    timestamp: str,
    prepared_answer_interpretation: PreparedAnswerInterpretation | None = None,
) -> ResponseDraft:
    """Route one chat request to deterministic handling or fallback tutor handling."""
    match chat_intent(request.text):
        case "help":
            return ResponseDraft(text=_HELP_TEXT, topic_tags=("help",))
        case "progress":
            return ResponseDraft(
                text=progress_response(dependencies, learner_handle),
                topic_tags=("progress",),
            )
        case "now":
            response_text, tier_promotions = now_response(
                dependencies,
                learner_handle,
                request.context.source,
                timestamp,
            )
            return ResponseDraft(
                text=response_text,
                topic_tags=(chat_intent(request.text),),
                public_announcements=format_tier_promotion_announcements(tier_promotions),
            )
        case "check":
            response = check_response(
                dependencies,
                learner_handle,
                request.context.source,
                timestamp,
                is_answer=False,
            )
            return ResponseDraft(
                text=response.text,
                topic_tags=("check",),
                retry_after_irc_client_verification=response.retry_after_irc_client_verification,
                public_announcements=format_tier_promotion_announcements(
                    response.tier_promotions,
                ),
            )
        case "answer":
            response = check_response(
                dependencies,
                learner_handle,
                request.context.source,
                timestamp,
                answer_text=answer_text(request.text),
                prepared_answer_interpretation=prepared_answer_interpretation,
                is_answer=True,
            )
            return ResponseDraft(
                text=response.text,
                topic_tags=("answer", "check"),
                retry_after_irc_client_verification=response.retry_after_irc_client_verification,
                restricted_llm_audit_log=(
                    None
                    if prepared_answer_interpretation is None
                    else prepared_answer_interpretation.restricted_llm_audit_log
                ),
                public_announcements=format_tier_promotion_announcements(
                    response.tier_promotions,
                ),
            )
        case "thank":
            response_text, tier_promotions = thank_response(
                dependencies,
                learner_handle,
                request.text,
                timestamp,
                request.context.source,
            )
            return ResponseDraft(
                text=response_text,
                topic_tags=("thank",),
                public_announcements=format_tier_promotion_announcements(tier_promotions),
            )
        case "freeform":
            if routes_bare_interactive_answer(request, dependencies, learner_handle):
                response = check_response(
                    dependencies,
                    learner_handle,
                    request.context.source,
                    timestamp,
                    answer_text=request.text,
                    prepared_answer_interpretation=prepared_answer_interpretation,
                    is_answer=True,
                )
                return ResponseDraft(
                    text=response.text,
                    topic_tags=("answer", "check"),
                    retry_after_irc_client_verification=response.retry_after_irc_client_verification,
                    restricted_llm_audit_log=(
                        None
                        if prepared_answer_interpretation is None
                        else prepared_answer_interpretation.restricted_llm_audit_log
                    ),
                    public_announcements=format_tier_promotion_announcements(
                        response.tier_promotions,
                    ),
                )
            return freeform_response_draft(request, dependencies, learner_handle, timestamp)
