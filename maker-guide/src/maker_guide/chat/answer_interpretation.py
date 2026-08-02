"""Read-only semantic answer interpretation before progress transactions."""

from __future__ import annotations

from typing import Literal, cast

from maker_guide.chat.contract import (
    ChatDependencies,
    ChatRequest,
    PreparedAnswerInterpretation,
    RestrictedLlmAuditLogInput,
)
from maker_guide.chat.intents import answer_text, chat_intent
from maker_guide.chat.snapshot import build_learner_snapshot
from maker_guide.chat.tutor import routes_bare_interactive_answer
from maker_guide.curriculum.models import (
    AllOfValidation,
    AnswerConceptAssessment,
    InteractiveQuestionValidation,
    QuestValidation,
    SessionObjectiveValidation,
)
from maker_guide.llm_tutor import (
    MAX_ANSWER_EVIDENCE_QUOTE_LENGTH,
    AnswerInterpretationRequest,
    AnswerVerdict,
    SemanticConceptRubric,
    TutorError,
    TutorRateLimitError,
    safe_tutor_text,
)
from maker_guide.progress.models import ProgressServiceError
from maker_guide.progress.service import current_session_objective

_ANSWER_INTERPRETATION_MAX_TOKENS = 800


def prepare_answer_interpretation(
    request: ChatRequest,
    dependencies: ChatDependencies,
    learner_handle: str,
) -> PreparedAnswerInterpretation | None:
    """Interpret one private answer without holding a SQLite transaction."""
    if request.visibility != "private" or dependencies.answer_interpreter is None:
        return None
    learner_answer = _learner_answer(request, dependencies, learner_handle)
    if learner_answer is None:
        return None
    target = _answer_target(dependencies, learner_handle)
    if target is None:
        return None
    target_type, target_id, target_session_id, validation = target
    interactive_validation = _interactive_validation(validation)
    if interactive_validation is None:
        return None
    interpretation_request = AnswerInterpretationRequest(
        learner_handle=learner_handle,
        question=interactive_validation.question,
        answer=learner_answer,
        concept_rubrics=tuple(
            SemanticConceptRubric(concept_id=concept.id, rubric=concept.rubric)
            for concept in interactive_validation.required_concepts
        ),
        max_tokens=min(dependencies.tutor_max_tokens, _ANSWER_INTERPRETATION_MAX_TOKENS),
    )
    try:
        interpretation = dependencies.answer_interpreter.interpret_answer(interpretation_request)
        assessments = _validated_assessments(
            interpretation.components,
            interpretation_request,
        )
    except TutorError as error:
        return PreparedAnswerInterpretation(
            target_type=target_type,
            target_id=target_id,
            target_session_id=target_session_id,
            assessments=(),
            feedback=None,
            restricted_llm_audit_log=RestrictedLlmAuditLogInput(
                provider="unavailable",
                model="unavailable",
                status=(
                    "answer_interpretation_rate_limited"
                    if isinstance(error, TutorRateLimitError)
                    else "answer_interpretation_failed"
                ),
                request_payload=_request_payload(interpretation_request),
                response_payload={"reason": str(error)},
            ),
        )
    return PreparedAnswerInterpretation(
        target_type=target_type,
        target_id=target_id,
        target_session_id=target_session_id,
        assessments=assessments,
        feedback=(
            safe_tutor_text(interpretation.feedback)
            if interpretation.feedback is not None
            else None
        ),
        restricted_llm_audit_log=RestrictedLlmAuditLogInput(
            provider=interpretation.provider,
            model=interpretation.model,
            status="answer_interpreted",
            request_payload=_request_payload(interpretation_request),
            response_payload={
                "raw_arguments": interpretation.raw_arguments,
                "feedback": interpretation.feedback,
                "components": [
                    {
                        "concept_id": component.concept_id,
                        "verdict": component.verdict,
                        "evidence_quote": component.evidence_quote,
                    }
                    for component in interpretation.components
                ],
            },
        ),
    )


def _learner_answer(
    request: ChatRequest,
    dependencies: ChatDependencies,
    learner_handle: str,
) -> str | None:
    intent = chat_intent(request.text)
    if intent == "answer":
        return answer_text(request.text)
    if intent == "freeform" and routes_bare_interactive_answer(
        request,
        dependencies,
        learner_handle,
    ):
        return request.text
    return None


def _answer_target(
    dependencies: ChatDependencies,
    learner_handle: str,
) -> (
    tuple[
        Literal["quest", "session_objective"],
        str,
        str | None,
        QuestValidation | SessionObjectiveValidation,
    ]
    | None
):
    try:
        objective_result = current_session_objective(
            dependencies.database_connection,
            dependencies.catalog,
            handle=learner_handle,
        )
    except ProgressServiceError:
        return None
    if objective_result.objective is not None:
        return (
            "session_objective",
            objective_result.objective.id,
            objective_result.session_id,
            objective_result.objective.validation,
        )
    learner_snapshot = build_learner_snapshot(
        dependencies.database_connection,
        dependencies.catalog,
        learner_handle,
    )
    if not learner_snapshot.pending_quests:
        return None
    quest = dependencies.catalog.quest(learner_snapshot.pending_quests[0])
    return "quest", quest.id, None, quest.validation


def _interactive_validation(
    validation: QuestValidation | SessionObjectiveValidation,
) -> InteractiveQuestionValidation | None:
    if isinstance(validation, InteractiveQuestionValidation):
        return validation
    if isinstance(validation, AllOfValidation):
        for child_validation in validation.validations:
            if (result := _interactive_validation(child_validation)) is not None:
                return result
    return None


def _request_payload(request: AnswerInterpretationRequest) -> dict[str, object]:
    return {
        "operation": "answer_interpretation",
        "question": request.question,
        "answer": request.answer,
        "concept_rubrics": [
            {"concept_id": rubric.concept_id, "rubric": rubric.rubric}
            for rubric in request.concept_rubrics
        ],
        "max_tokens": request.max_tokens,
    }


def _validated_assessments(
    components: tuple[object, ...],
    request: AnswerInterpretationRequest,
) -> tuple[AnswerConceptAssessment, ...]:
    requested_ids = tuple(rubric.concept_id for rubric in request.concept_rubrics)
    components_by_id: dict[str, AnswerConceptAssessment] = {}
    for component in components:
        concept_id = getattr(component, "concept_id", None)
        verdict = getattr(component, "verdict", None)
        evidence_quote = getattr(component, "evidence_quote", None)
        if (
            not isinstance(concept_id, str)
            or verdict not in {"demonstrated", "contradicted", "not_demonstrated"}
            or concept_id in components_by_id
            or (verdict == "not_demonstrated") != (evidence_quote is None)
            or (
                evidence_quote is not None
                and (
                    not isinstance(evidence_quote, str)
                    or not evidence_quote
                    or len(evidence_quote) > MAX_ANSWER_EVIDENCE_QUOTE_LENGTH
                    or evidence_quote not in request.answer
                )
            )
        ):
            raise TutorError("answer interpreter returned invalid component analysis")
        components_by_id[concept_id] = AnswerConceptAssessment(
            concept_id=concept_id,
            verdict=cast("AnswerVerdict", verdict),
        )
    if set(components_by_id) != set(requested_ids):
        raise TutorError("answer interpreter returned the wrong concept set")
    return tuple(components_by_id[concept_id] for concept_id in requested_ids)
