"""Deterministic quest validation."""

from __future__ import annotations

import os
import re
import sqlite3
import stat
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from maker_guide.curriculum.models import (
    AllOfValidation,
    AnswerConcept,
    AnswerConceptAssessment,
    CommandHistoryValidation,
    CourseCatalog,
    ExecutablePathValidation,
    FileCheckValidation,
    FileMatchesPathValidation,
    InteractiveQuestionValidation,
    IrcChannelJoinObservedValidation,
    IrcCtcpVersionValidation,
    LearnerHandleQuestionValidation,
    OwnedPathValidation,
    PathExistsValidation,
    Quest,
    QuestValidation,
    QuestValidationLeaf,
    SessionObjectiveValidation,
    SshPublicKeyObservedValidation,
    UserPortFileValidation,
)
from maker_guide.repositories.audit_event import AuditEvent, list_recent_audit_events_by_type
from maker_guide.repositories.command_observation import (
    CommandObservation,
    list_recent_command_observations,
)
from maker_guide.repositories.helpers import JsonPayload
from maker_guide.validation_paths import (
    UnixAccountLookup,
    ValidationPathResolution,
    lookup_unix_account,
    open_validation_file,
    resolve_validation_path,
)

_OBSERVATION_LIMIT = 100
_AUDIT_EVENT_LIMIT = 20
_MAX_VALIDATION_FILE_BYTES = 1_048_576
_PATH_RESOLUTION_FAILURE_REASONS = frozenset(
    {
        "unknown-user",
        "unsafe-path",
        "path-escapes-scope",
        "missing-path",
        "broken-symlink",
        "symlink-loop",
        "permission-denied",
        "read-error",
    },
)
_FILE_READ_FAILURE_REASONS = frozenset(
    {
        "not-regular-file",
        "permission-denied",
        "file-too-large",
        "file-decode-error",
        "read-error",
    },
)
GENERIC_VALIDATION_FAILURE_REASONS = frozenset(
    {
        "incomplete-evidence",
        "missing-answer",
        "missing-concept",
        "contradicted-concept",
        "wrong-owner",
        "wrong-answer",
        "missing-command",
        "unsupported-validation",
        "unknown-user",
        "unsafe-path",
        "path-escapes-scope",
        "missing-path",
        "broken-symlink",
        "symlink-loop",
        "permission-denied",
        "read-error",
        "not-regular-file",
        "not-executable",
        "file-too-large",
        "file-decode-error",
        "file-content-mismatch",
        "forbidden-content-present",
        "invalid-regex",
        "port-content-mismatch",
        "unsupported-port-formula",
        "missing-irc-ctcp-version",
        "unsupported-irc-client",
    },
)
"""Failure reasons with generic learner-facing fallback copy."""
_VALIDATION_FAILURE_REASONS_BY_ID = {
    "command_history": frozenset({"missing-command"}),
    "path_exists": _PATH_RESOLUTION_FAILURE_REASONS,
    "executable_path": _PATH_RESOLUTION_FAILURE_REASONS
    | frozenset({"not-regular-file", "not-executable", "wrong-owner"}),
    "owned_path": _PATH_RESOLUTION_FAILURE_REASONS | frozenset({"not-regular-file", "wrong-owner"}),
    "file_check": _PATH_RESOLUTION_FAILURE_REASONS
    | _FILE_READ_FAILURE_REASONS
    | frozenset({"file-content-mismatch", "forbidden-content-present", "invalid-regex"}),
    "file_matches_path": _PATH_RESOLUTION_FAILURE_REASONS
    | _FILE_READ_FAILURE_REASONS
    | frozenset({"file-content-mismatch"}),
    "user_port_file": _PATH_RESOLUTION_FAILURE_REASONS
    | _FILE_READ_FAILURE_REASONS
    | frozenset({"port-content-mismatch", "invalid-regex", "unsupported-port-formula"}),
    "interactive_question": frozenset(
        {"missing-answer", "missing-concept", "contradicted-concept", "invalid-regex"},
    ),
    "learner_handle_question": frozenset({"missing-answer", "wrong-answer"}),
    "irc_ctcp_version": frozenset(
        {"missing-irc-ctcp-version", "unsupported-irc-client"},
    ),
}
_SUPPORTED_VALIDATION_TYPE_IDS = frozenset(
    {
        "command_history",
        "path_exists",
        "executable_path",
        "owned_path",
        "file_check",
        "file_matches_path",
        "user_port_file",
        "interactive_question",
        "learner_handle_question",
        "irc_ctcp_version",
    },
)


@dataclass(frozen=True, kw_only=True, slots=True)
class QuestValidationInput:
    """Input for one deterministic quest validation run."""

    database_connection: sqlite3.Connection
    """SQLite connection used to read deterministic evidence."""
    catalog: CourseCatalog
    """Course catalog that owns the quest being checked."""
    handle: str
    """Learner handle being checked."""
    quest: Quest | None = None
    """Quest being validated."""
    checked_at: str
    """ISO timestamp for this validation check."""
    assigned_at: str
    """ISO timestamp for when the checked quest was assigned."""
    answer_text: str | None = None
    """Optional learner answer for answer-based validation rules."""
    answer_concept_assessments: tuple[AnswerConceptAssessment, ...] = ()
    """Strictly validated semantic assessments from the read-only interpreter."""
    account_lookup: UnixAccountLookup = lookup_unix_account
    """Unix account lookup used by filesystem validation rules."""


@dataclass(frozen=True, kw_only=True, slots=True)
class QuestValidationResult:
    """Result of deterministic validation before progress service writes."""

    passed: bool
    """Whether the learner evidence satisfies the quest validation."""
    failure_reason: str | None
    """Stable failure reason for failed attempts."""
    evidence: JsonPayload
    """Non-answer-revealing facts recorded with the quest attempt."""


@dataclass(frozen=True, kw_only=True, slots=True)
class QuestValidationSupport:
    """Runtime support status for one validation tree."""

    supported: bool
    """Whether every validation leaf has runtime support."""
    unsupported_validation_types: tuple[str, ...]
    """Unsupported validation type ids in deterministic order."""


@dataclass(frozen=True, kw_only=True, slots=True)
class _ValidationPathCheckResult:
    catalog_path: str
    passed: bool
    failure_reason: str | None
    evidence: JsonPayload


@dataclass(frozen=True, kw_only=True, slots=True)
class _ValidationFileRead:
    file_contents: str | None
    byte_count: int | None
    failure_reason: str | None


@dataclass(frozen=True, kw_only=True, slots=True)
class _ValidationFileBytes:
    content_bytes: bytes | None
    failure_reason: str | None


@dataclass(frozen=True, kw_only=True, slots=True)
class _FileRegexValidationRequest:
    validation_type: str
    catalog_path: str
    required_regex: str
    mismatch_failure_reason: str
    forbidden_regex: str | None = None
    extra_evidence: JsonPayload | None = None


@dataclass(frozen=True, kw_only=True, slots=True)
class _AnswerConceptCheck:
    concept_id: str
    matched: bool
    contradicted: bool
    invalid_regex: bool = False


def validate_quest(validation_input: QuestValidationInput) -> QuestValidationResult:
    """Validate a quest using deterministic evidence only."""
    if validation_input.quest is None:
        raise ValueError("quest validation requires a quest")
    return _validate_rule(validation_input, validation_input.quest.validation)


def validate_session_objective(
    validation_input: QuestValidationInput,
    validation: SessionObjectiveValidation,
) -> QuestValidationResult:
    """Validate dedicated session-objective evidence."""
    if isinstance(validation, SshPublicKeyObservedValidation):
        events = list_recent_audit_events_by_type(
            validation_input.database_connection,
            "ssh_publickey_observed",
            validation_input.handle,
            validation_input.assigned_at,
            _AUDIT_EVENT_LIMIT,
            created_through=validation_input.checked_at,
        )
        event = events[0] if events else None
        return QuestValidationResult(
            passed=event is not None,
            failure_reason=None if event is not None else "missing-ssh-publickey",
            evidence=_validation_evidence(
                "ssh_publickey_observed",
                event is not None,
                None if event is not None else "missing-ssh-publickey",
                audit_event_id=event.id if event is not None else None,
            ),
        )
    if not isinstance(validation, IrcChannelJoinObservedValidation):
        return _validate_rule(validation_input, validation)
    events = list_recent_audit_events_by_type(
        validation_input.database_connection,
        "irc_channel_joined",
        validation_input.handle,
        validation_input.assigned_at,
        _AUDIT_EVENT_LIMIT,
        created_through=validation_input.checked_at,
    )
    event = next(
        (
            event
            for event in events
            if isinstance(channel := event.payload.get("channel"), str)
            and channel.casefold() == validation.channel.casefold()
        ),
        None,
    )
    return QuestValidationResult(
        passed=event is not None,
        failure_reason=None if event is not None else "missing-irc-channel-join",
        evidence=_validation_evidence(
            "irc_channel_joined",
            event is not None,
            None if event is not None else "missing-irc-channel-join",
            audit_event_id=event.id if event is not None else None,
            channel=validation.channel,
        ),
    )


def validation_support(validation: QuestValidation) -> QuestValidationSupport:
    """Return runtime support status for a validation tree."""
    unsupported_validation_types = _unsupported_validation_types(validation)
    return QuestValidationSupport(
        supported=not unsupported_validation_types,
        unsupported_validation_types=tuple(sorted(unsupported_validation_types)),
    )


def validation_failure_reasons(validation: QuestValidation) -> frozenset[str]:
    """Return stable failure reasons the runtime can emit for a validation tree."""
    if isinstance(validation, AllOfValidation):
        return frozenset(
            failure_reason
            for child_validation in validation.validations
            for failure_reason in validation_failure_reasons(child_validation)
        ) | frozenset({"incomplete-evidence"})
    if isinstance(validation, FileCheckValidation):
        failure_reasons = _VALIDATION_FAILURE_REASONS_BY_ID["file_check"]
        if validation.forbidden_regex is None:
            failure_reasons -= frozenset({"forbidden-content-present"})
        return failure_reasons
    if isinstance(validation, FileMatchesPathValidation):
        return _VALIDATION_FAILURE_REASONS_BY_ID["file_matches_path"]
    if isinstance(validation, InteractiveQuestionValidation):
        failure_reasons = _VALIDATION_FAILURE_REASONS_BY_ID["interactive_question"]
        if not any(concept.forbidden_patterns for concept in validation.required_concepts):
            failure_reasons -= frozenset({"contradicted-concept"})
        return failure_reasons
    if isinstance(validation, UserPortFileValidation) and validation.port_formula == "10000+uid":
        return _VALIDATION_FAILURE_REASONS_BY_ID["user_port_file"] - frozenset(
            {"unsupported-port-formula"},
        )
    return _VALIDATION_FAILURE_REASONS_BY_ID.get(
        _validation_type_id(validation),
        frozenset({"unsupported-validation"}),
    )


def _validate_rule(  # noqa: C901
    validation_input: QuestValidationInput,
    validation: QuestValidationLeaf | AllOfValidation,
) -> QuestValidationResult:
    match validation:
        case CommandHistoryValidation():
            result = _validate_command_history(validation_input, validation)
        case PathExistsValidation():
            result = _validate_path_exists(validation_input, validation)
        case ExecutablePathValidation():
            result = _validate_executable_paths(validation_input, validation)
        case OwnedPathValidation():
            result = _validate_owned_path(validation_input, validation)
        case FileCheckValidation():
            result = _validate_file_check(validation_input, validation)
        case FileMatchesPathValidation():
            result = _validate_file_matches_path(validation_input, validation)
        case UserPortFileValidation():
            result = _validate_user_port_file(validation_input, validation)
        case InteractiveQuestionValidation():
            result = _validate_interactive_question(validation_input, validation)
        case LearnerHandleQuestionValidation():
            result = _validate_learner_handle_question(validation_input)
        case IrcCtcpVersionValidation():
            result = _validate_irc_ctcp_version(validation_input, validation)
        case AllOfValidation(validations=validations):
            result = _validate_all_of(validation_input, validations)
    return result


def _validate_command_history(
    validation_input: QuestValidationInput,
    validation: CommandHistoryValidation,
) -> QuestValidationResult:
    observations = list_recent_command_observations(
        validation_input.database_connection,
        validation_input.handle,
        validation_input.catalog.course.id,
        observed_since=validation_input.assigned_at,
        limit=_OBSERVATION_LIMIT,
        observed_through=validation_input.checked_at,
    )
    if validation.ordered:
        remaining_observations = iter(reversed(observations))
        matched_observations = tuple(
            _first_matching_command_observation(required_pattern, remaining_observations)
            for required_pattern in validation.required_patterns
        )
    else:
        matched_observations = tuple(
            _first_matching_command_observation(required_pattern, observations)
            for required_pattern in validation.required_patterns
        )
    passed = all(observation is not None for observation in matched_observations)
    if len(validation.observed_commands) == len(matched_observations):
        matched_commands = [
            observed_command
            for observed_command, observation in zip(
                validation.observed_commands,
                matched_observations,
                strict=True,
            )
            if observation is not None
        ]
        missing_commands = [
            observed_command
            for observed_command, observation in zip(
                validation.observed_commands,
                matched_observations,
                strict=True,
            )
            if observation is None
        ]
    else:
        matched_commands = list(validation.observed_commands) if passed else []
        missing_commands = [] if passed else list(validation.observed_commands)
    failure_reason = None if passed else "missing-command"
    return QuestValidationResult(
        passed=passed,
        failure_reason=failure_reason,
        evidence=_validation_evidence(
            "command_history",
            passed,
            failure_reason,
            matched_count=sum(observation is not None for observation in matched_observations),
            matched_commands=matched_commands,
            matched_observation_ids=_matched_command_observation_ids(matched_observations),
            missing_commands=missing_commands,
            observed_count=len(observations),
            observed_since=validation_input.assigned_at,
            required_count=len(validation.required_patterns),
        ),
    )


def _first_matching_command_observation(
    required_pattern: str,
    observations: Iterable[CommandObservation],
) -> CommandObservation | None:
    for observation in observations:
        command = " ".join(observation.command.split())
        if re.search(required_pattern, command) is not None:
            return observation
    return None


def _matched_command_observation_ids(
    observations: tuple[CommandObservation | None, ...],
) -> list[int]:
    matched_ids: list[int] = []
    for observation in observations:
        if (
            observation is not None
            and observation.id is not None
            and observation.id not in matched_ids
        ):
            matched_ids.append(observation.id)
    return matched_ids


def _validate_interactive_question(
    validation_input: QuestValidationInput,
    validation: InteractiveQuestionValidation,
) -> QuestValidationResult:
    normalized_answer = _normalized_answer(validation_input.answer_text)
    if normalized_answer is None:
        return _interactive_question_result(validation, False, "missing-answer", ())

    assessments_by_id = {
        assessment.concept_id: assessment
        for assessment in validation_input.answer_concept_assessments
    }
    if set(assessments_by_id) != {concept.id for concept in validation.required_concepts}:
        assessments_by_id = {}
    concept_checks = tuple(
        _check_answer_concept(normalized_answer, concept, assessments_by_id.get(concept.id))
        for concept in validation.required_concepts
    )
    if any(concept_check.invalid_regex for concept_check in concept_checks):
        failure_reason = "invalid-regex"
    elif any(concept_check.contradicted for concept_check in concept_checks):
        failure_reason = "contradicted-concept"
    elif not all(concept_check.matched for concept_check in concept_checks):
        failure_reason = "missing-concept"
    else:
        failure_reason = None
    return _interactive_question_result(
        validation,
        failure_reason is None,
        failure_reason,
        concept_checks,
    )


def _normalized_answer(answer_text: str | None) -> str | None:
    if answer_text is None:
        return None
    normalized_answer = " ".join(answer_text.casefold().split())
    return normalized_answer or None


def _check_answer_concept(
    normalized_answer: str,
    concept: AnswerConcept,
    semantic_assessment: AnswerConceptAssessment | None = None,
) -> _AnswerConceptCheck:
    try:
        matched = any(re.search(alias, normalized_answer) is not None for alias in concept.aliases)
        contradicted = any(
            re.search(forbidden_pattern, normalized_answer) is not None
            for forbidden_pattern in concept.forbidden_patterns
        )
    except re.error:
        return _AnswerConceptCheck(
            concept_id=concept.id,
            matched=False,
            contradicted=False,
            invalid_regex=True,
        )
    return _AnswerConceptCheck(
        concept_id=concept.id,
        matched=matched
        or (semantic_assessment is not None and semantic_assessment.verdict == "demonstrated"),
        contradicted=contradicted
        or (semantic_assessment is not None and semantic_assessment.verdict == "contradicted"),
    )


def _interactive_question_result(
    validation: InteractiveQuestionValidation,
    passed: bool,
    failure_reason: str | None,
    concept_checks: tuple[_AnswerConceptCheck, ...],
) -> QuestValidationResult:
    matched_concept_ids = [
        concept_check.concept_id for concept_check in concept_checks if concept_check.matched
    ]
    contradicted_concept_ids = [
        concept_check.concept_id for concept_check in concept_checks if concept_check.contradicted
    ]
    missing_concept_ids = [
        concept.id
        for concept in validation.required_concepts
        if concept.id not in frozenset(matched_concept_ids)
    ]
    return QuestValidationResult(
        passed=passed,
        failure_reason=failure_reason,
        evidence=_validation_evidence(
            "interactive_question",
            passed,
            failure_reason,
            answer_present=bool(concept_checks),
            expected_concept_count=len(validation.required_concepts),
            matched_concept_count=len(matched_concept_ids),
            contradicted_concept_count=len(contradicted_concept_ids),
            matched_concept_ids=matched_concept_ids,
            missing_concept_ids=missing_concept_ids,
            contradicted_concept_ids=contradicted_concept_ids,
        ),
    )


def _validate_learner_handle_question(
    validation_input: QuestValidationInput,
) -> QuestValidationResult:
    normalized_answer = _normalized_answer(validation_input.answer_text)
    if normalized_answer is None:
        return _learner_handle_question_result(False, "missing-answer", False)
    handle_matched = normalized_answer == _normalized_answer(validation_input.handle)
    return _learner_handle_question_result(
        handle_matched,
        None if handle_matched else "wrong-answer",
        handle_matched,
    )


def _validate_irc_ctcp_version(
    validation_input: QuestValidationInput,
    validation: IrcCtcpVersionValidation,
) -> QuestValidationResult:
    events = list_recent_audit_events_by_type(
        validation_input.database_connection,
        "irc_ctcp_version",
        validation_input.handle,
        validation_input.assigned_at,
        _AUDIT_EVENT_LIMIT,
        created_through=validation_input.checked_at,
    )
    if not events:
        return _irc_ctcp_version_result(
            False,
            "missing-irc-ctcp-version",
            None,
            None,
            validation.accepted_clients,
        )
    matched_event = _first_accepted_irc_ctcp_event(events, validation.accepted_clients)
    if matched_event is None:
        return _irc_ctcp_version_result(
            False,
            "unsupported-irc-client",
            events[0],
            _payload_string(events[0].payload, "version"),
            validation.accepted_clients,
        )
    return _irc_ctcp_version_result(
        True,
        None,
        matched_event,
        _payload_string(matched_event.payload, "version"),
        validation.accepted_clients,
    )


def _first_accepted_irc_ctcp_event(
    events: list[AuditEvent],
    accepted_clients: tuple[str, ...],
) -> AuditEvent | None:
    for event in events:
        version = _payload_string(event.payload, "version")
        if version is not None and _irc_client_is_accepted(version, accepted_clients):
            return event
    return None


def _irc_client_is_accepted(version: str, accepted_clients: tuple[str, ...]) -> bool:
    normalized_version = version.casefold()
    return any(client.casefold() in normalized_version for client in accepted_clients)


def _payload_string(payload: JsonPayload, key: str) -> str | None:
    value = payload.get(key)
    return value if isinstance(value, str) else None


def _irc_ctcp_version_result(
    passed: bool,
    failure_reason: str | None,
    event: AuditEvent | None,
    version: str | None,
    accepted_clients: tuple[str, ...],
) -> QuestValidationResult:
    return QuestValidationResult(
        passed=passed,
        failure_reason=failure_reason,
        evidence=_validation_evidence(
            "irc_ctcp_version",
            passed,
            failure_reason,
            accepted_clients=list(accepted_clients),
            audit_event_id=event.id if event is not None else None,
            version=version,
        ),
    )


def _learner_handle_question_result(
    passed: bool,
    failure_reason: str | None,
    handle_matched: bool,
) -> QuestValidationResult:
    return QuestValidationResult(
        passed=passed,
        failure_reason=failure_reason,
        evidence=_validation_evidence(
            "learner_handle_question",
            passed,
            failure_reason,
            answer_present=failure_reason != "missing-answer",
            expected_handle_matched=handle_matched,
        ),
    )


def _validate_path_exists(
    validation_input: QuestValidationInput,
    validation: PathExistsValidation,
) -> QuestValidationResult:
    path_results = tuple(
        _validate_existing_path(validation_input, catalog_path) for catalog_path in validation.paths
    )
    passed = all(path_result.passed for path_result in path_results)
    failure_reason = None if passed else _first_path_check_failure_reason(path_results)
    return QuestValidationResult(
        passed=passed,
        failure_reason=failure_reason,
        evidence=_validation_evidence(
            "path_exists",
            passed,
            failure_reason,
            required_count=len(validation.paths),
            existing_count=sum(path_result.passed for path_result in path_results),
            paths=[path_result.evidence for path_result in path_results],
        ),
    )


def _validate_executable_paths(
    validation_input: QuestValidationInput,
    validation: ExecutablePathValidation,
) -> QuestValidationResult:
    path_results = tuple(
        _validate_executable_path(validation_input, catalog_path)
        for catalog_path in validation.paths
    )
    passed = all(path_result.passed for path_result in path_results)
    failure_reason = None if passed else _first_path_check_failure_reason(path_results)
    return QuestValidationResult(
        passed=passed,
        failure_reason=failure_reason,
        evidence=_validation_evidence(
            "executable_path",
            passed,
            failure_reason,
            required_count=len(validation.paths),
            executable_count=sum(path_result.passed for path_result in path_results),
            paths=[path_result.evidence for path_result in path_results],
        ),
    )


def _validate_owned_path(  # noqa: PLR0911
    validation_input: QuestValidationInput,
    validation: OwnedPathValidation,
) -> QuestValidationResult:
    opened_file = open_validation_file(
        validation_input.handle,
        validation.path,
        account_lookup=validation_input.account_lookup,
    )
    if opened_file.failure_reason is not None:
        return _owned_path_result(validation.path, False, opened_file.failure_reason)
    if opened_file.file_descriptor is None:
        return _owned_path_result(validation.path, False, "read-error")
    try:
        path_status = os.fstat(opened_file.file_descriptor)
    except OSError:
        return _owned_path_result(validation.path, False, "read-error")
    finally:
        os.close(opened_file.file_descriptor)
    unix_account = validation_input.account_lookup(validation_input.handle)
    if unix_account is None:
        return _owned_path_result(validation.path, False, "unknown-user")
    if not stat.S_ISREG(path_status.st_mode):
        return _owned_path_result(validation.path, False, "not-regular-file")
    if path_status.st_uid != unix_account.user_id:
        return _owned_path_result(validation.path, False, "wrong-owner")
    return _owned_path_result(validation.path, True, None)


def _validate_file_check(
    validation_input: QuestValidationInput,
    validation: FileCheckValidation,
) -> QuestValidationResult:
    return _validate_file_regex(
        validation_input,
        _FileRegexValidationRequest(
            validation_type="file_check",
            catalog_path=validation.path,
            required_regex=validation.required_regex,
            mismatch_failure_reason="file-content-mismatch",
            forbidden_regex=validation.forbidden_regex,
        ),
    )


def _validate_file_matches_path(
    validation_input: QuestValidationInput,
    validation: FileMatchesPathValidation,
) -> QuestValidationResult:
    opened_file = open_validation_file(
        validation_input.handle,
        validation.path,
        account_lookup=validation_input.account_lookup,
    )
    if opened_file.failure_reason is not None:
        return _file_validation_result(
            "file_matches_path", validation.path, False, opened_file.failure_reason
        )
    if opened_file.file_descriptor is None:
        return _file_validation_result("file_matches_path", validation.path, False, "read-error")
    try:
        target_bytes = _read_comparison_file(opened_file.file_descriptor)
    finally:
        os.close(opened_file.file_descriptor)
    if target_bytes.failure_reason is not None:
        return _file_validation_result(
            "file_matches_path",
            validation.path,
            False,
            target_bytes.failure_reason,
            byte_count=(
                len(target_bytes.content_bytes) if target_bytes.content_bytes is not None else None
            ),
        )
    try:
        source_bytes = Path(validation.source_path).read_bytes()
    except OSError:
        return _file_validation_result("file_matches_path", validation.path, False, "read-error")
    if len(source_bytes) > _MAX_VALIDATION_FILE_BYTES:
        return _file_validation_result(
            "file_matches_path", validation.path, False, "file-too-large"
        )
    return _file_validation_result(
        "file_matches_path",
        validation.path,
        target_bytes.content_bytes == source_bytes,
        None if target_bytes.content_bytes == source_bytes else "file-content-mismatch",
        byte_count=(
            len(target_bytes.content_bytes) if target_bytes.content_bytes is not None else None
        ),
        source_path=validation.source_path,
    )


def _read_comparison_file(file_descriptor: int) -> _ValidationFileBytes:
    if failure_reason := _regular_file_failure_reason(file_descriptor):
        return _ValidationFileBytes(content_bytes=None, failure_reason=failure_reason)
    comparison_bytes = _read_validation_file_bytes(file_descriptor)
    if (
        comparison_bytes.content_bytes is not None
        and len(comparison_bytes.content_bytes) > _MAX_VALIDATION_FILE_BYTES
    ):
        return _ValidationFileBytes(content_bytes=None, failure_reason="file-too-large")
    return comparison_bytes


def _validate_user_port_file(
    validation_input: QuestValidationInput,
    validation: UserPortFileValidation,
) -> QuestValidationResult:
    if validation.port_formula != "10000+uid":
        return QuestValidationResult(
            passed=False,
            failure_reason="unsupported-port-formula",
            evidence=_validation_evidence(
                "user_port_file",
                False,
                "unsupported-port-formula",
                catalog_path=validation.path,
                port_formula=validation.port_formula,
            ),
        )
    unix_account = validation_input.account_lookup(validation_input.handle)
    if unix_account is None:
        return QuestValidationResult(
            passed=False,
            failure_reason="unknown-user",
            evidence=_validation_evidence(
                "user_port_file",
                False,
                "unknown-user",
                catalog_path=validation.path,
                port_formula=validation.port_formula,
            ),
        )
    computed_port = 10000 + unix_account.user_id
    return _validate_file_regex(
        validation_input,
        _FileRegexValidationRequest(
            validation_type="user_port_file",
            catalog_path=validation.path,
            required_regex=validation.required_regex_template.replace("{port}", str(computed_port)),
            mismatch_failure_reason="port-content-mismatch",
            extra_evidence={
                "port_formula": validation.port_formula,
                "computed_port": computed_port,
            },
        ),
    )


def _validate_all_of(
    validation_input: QuestValidationInput,
    validations: tuple[QuestValidationLeaf, ...],
) -> QuestValidationResult:
    child_results = tuple(
        _validate_rule(validation_input, child_validation) for child_validation in validations
    )
    passed = all(child_result.passed for child_result in child_results)
    failure_reason = None if passed else _first_failure_reason(child_results)
    return QuestValidationResult(
        passed=passed,
        failure_reason=failure_reason,
        evidence=_validation_evidence(
            "all_of",
            passed,
            failure_reason,
            checks=[child_result.evidence for child_result in child_results],
        ),
    )


def _first_failure_reason(results: tuple[QuestValidationResult, ...]) -> str:
    for result in results:
        if not result.passed and result.failure_reason is not None:
            return result.failure_reason
    return "incomplete-evidence"


def _validate_existing_path(
    validation_input: QuestValidationInput,
    catalog_path: str,
) -> _ValidationPathCheckResult:
    return _path_check_result_from_resolution(
        _resolve_validation_path(validation_input, catalog_path),
    )


def _validate_executable_path(
    validation_input: QuestValidationInput,
    catalog_path: str,
) -> _ValidationPathCheckResult:
    resolution = _resolve_validation_path(validation_input, catalog_path)
    if resolution.failure_reason is not None:
        return _path_check_result_from_resolution(resolution)
    if resolution.target_path is None:
        return _path_check_result(catalog_path, False, "read-error")
    try:
        path_status = resolution.target_path.stat()
    except PermissionError:
        return _path_check_result(catalog_path, False, "permission-denied")
    except OSError:
        return _path_check_result(catalog_path, False, "read-error")
    unix_account = validation_input.account_lookup(validation_input.handle)
    if unix_account is None:
        return _path_check_result(catalog_path, False, "unknown-user")
    return _executable_path_status_check(catalog_path, path_status, unix_account.user_id)


def _executable_path_status_check(
    catalog_path: str,
    path_status: os.stat_result,
    user_id: int,
) -> _ValidationPathCheckResult:
    if not stat.S_ISREG(path_status.st_mode):
        return _path_check_result(catalog_path, False, "not-regular-file")
    if path_status.st_uid != user_id:
        return _path_check_result(catalog_path, False, "wrong-owner")
    return _path_check_result(
        catalog_path,
        path_status.st_mode & stat.S_IXUSR != 0,
        None if path_status.st_mode & stat.S_IXUSR != 0 else "not-executable",
    )


def _validate_file_regex(
    validation_input: QuestValidationInput,
    request: _FileRegexValidationRequest,
) -> QuestValidationResult:
    opened_file = open_validation_file(
        validation_input.handle,
        request.catalog_path,
        account_lookup=validation_input.account_lookup,
    )
    if opened_file.failure_reason is not None:
        return _file_validation_result(
            request.validation_type,
            request.catalog_path,
            False,
            opened_file.failure_reason,
            **(request.extra_evidence or {}),
        )
    if opened_file.file_descriptor is None:
        return _file_validation_result(
            request.validation_type,
            request.catalog_path,
            False,
            "read-error",
            **(request.extra_evidence or {}),
        )
    try:
        file_read = _read_validation_file(opened_file.file_descriptor)
    finally:
        os.close(opened_file.file_descriptor)
    if file_read.failure_reason is not None:
        return _file_validation_result(
            request.validation_type,
            request.catalog_path,
            False,
            file_read.failure_reason,
            byte_count=file_read.byte_count,
            **(request.extra_evidence or {}),
        )
    file_contents = file_read.file_contents
    if file_contents is None:
        return _file_validation_result(
            request.validation_type,
            request.catalog_path,
            False,
            "read-error",
            byte_count=file_read.byte_count,
            **(request.extra_evidence or {}),
        )
    return _validate_file_regex_contents(request, file_read, file_contents)


def _validate_file_regex_contents(
    request: _FileRegexValidationRequest,
    file_read: _ValidationFileRead,
    file_contents: str,
) -> QuestValidationResult:
    try:
        required_matched = re.search(request.required_regex, file_contents) is not None
    except re.error:
        return _file_validation_result(
            request.validation_type,
            request.catalog_path,
            False,
            "invalid-regex",
            byte_count=file_read.byte_count,
            **(request.extra_evidence or {}),
        )
    forbidden_matched = _forbidden_regex_matched(request, file_contents)
    if forbidden_matched is None:
        return _file_validation_result(
            request.validation_type,
            request.catalog_path,
            False,
            "invalid-regex",
            byte_count=file_read.byte_count,
            required_matched=required_matched,
            **(request.extra_evidence or {}),
        )
    if not required_matched:
        return _file_validation_result(
            request.validation_type,
            request.catalog_path,
            False,
            request.mismatch_failure_reason,
            byte_count=file_read.byte_count,
            required_matched=required_matched,
            forbidden_matched=forbidden_matched if request.forbidden_regex is not None else None,
            **(request.extra_evidence or {}),
        )
    if forbidden_matched:
        return _file_validation_result(
            request.validation_type,
            request.catalog_path,
            False,
            "forbidden-content-present",
            byte_count=file_read.byte_count,
            required_matched=required_matched,
            forbidden_matched=forbidden_matched,
            **(request.extra_evidence or {}),
        )
    return _file_validation_result(
        request.validation_type,
        request.catalog_path,
        True,
        None,
        byte_count=file_read.byte_count,
        required_matched=required_matched,
        forbidden_matched=forbidden_matched if request.forbidden_regex is not None else None,
        **(request.extra_evidence or {}),
    )


def _forbidden_regex_matched(
    request: _FileRegexValidationRequest,
    file_contents: str,
) -> bool | None:
    if request.forbidden_regex is None:
        return False
    try:
        return re.search(request.forbidden_regex, file_contents) is not None
    except re.error:
        return None


def _read_validation_file(file_descriptor: int) -> _ValidationFileRead:
    if failure_reason := _regular_file_failure_reason(file_descriptor):
        return _ValidationFileRead(
            file_contents=None,
            byte_count=None,
            failure_reason=failure_reason,
        )
    validation_file_bytes = _read_validation_file_bytes(file_descriptor)
    if validation_file_bytes.failure_reason is not None:
        return _ValidationFileRead(
            file_contents=None,
            byte_count=None,
            failure_reason=validation_file_bytes.failure_reason,
        )
    content_bytes = validation_file_bytes.content_bytes
    if content_bytes is None:
        return _ValidationFileRead(file_contents=None, byte_count=None, failure_reason="read-error")
    if len(content_bytes) > _MAX_VALIDATION_FILE_BYTES:
        return _ValidationFileRead(
            file_contents=None,
            byte_count=len(content_bytes),
            failure_reason="file-too-large",
        )
    try:
        file_contents = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return _ValidationFileRead(
            file_contents=None,
            byte_count=len(content_bytes),
            failure_reason="file-decode-error",
        )
    return _ValidationFileRead(
        file_contents=file_contents,
        byte_count=len(content_bytes),
        failure_reason=None,
    )


def _regular_file_failure_reason(file_descriptor: int) -> str | None:
    try:
        if not stat.S_ISREG(os.fstat(file_descriptor).st_mode):
            return "not-regular-file"
    except PermissionError:
        return "permission-denied"
    except OSError:
        return "read-error"
    return None


def _read_validation_file_bytes(file_descriptor: int) -> _ValidationFileBytes:
    try:
        content_bytes = os.read(file_descriptor, _MAX_VALIDATION_FILE_BYTES + 1)
    except PermissionError:
        return _ValidationFileBytes(
            content_bytes=None,
            failure_reason="permission-denied",
        )
    except OSError:
        return _ValidationFileBytes(content_bytes=None, failure_reason="read-error")
    return _ValidationFileBytes(
        content_bytes=content_bytes,
        failure_reason=None,
    )


def _resolve_validation_path(
    validation_input: QuestValidationInput,
    catalog_path: str,
) -> ValidationPathResolution:
    return resolve_validation_path(
        validation_input.handle,
        catalog_path,
        account_lookup=validation_input.account_lookup,
    )


def _path_check_result_from_resolution(
    resolution: ValidationPathResolution,
) -> _ValidationPathCheckResult:
    return _path_check_result(
        resolution.catalog_path,
        resolution.failure_reason is None,
        resolution.failure_reason,
    )


def _path_check_result(
    catalog_path: str,
    passed: bool,
    failure_reason: str | None,
) -> _ValidationPathCheckResult:
    return _ValidationPathCheckResult(
        catalog_path=catalog_path,
        passed=passed,
        failure_reason=failure_reason,
        evidence={
            "catalog_path": catalog_path,
            "passed": passed,
            "failure_reason": failure_reason,
        },
    )


def _owned_path_result(
    catalog_path: str,
    passed: bool,
    failure_reason: str | None,
) -> QuestValidationResult:
    return QuestValidationResult(
        passed=passed,
        failure_reason=failure_reason,
        evidence=_validation_evidence(
            "owned_path",
            passed,
            failure_reason,
            catalog_path=catalog_path,
            path_category=_validation_path_category(catalog_path),
        ),
    )


def _first_path_check_failure_reason(
    path_results: tuple[_ValidationPathCheckResult, ...],
) -> str:
    for path_result in path_results:
        if path_result.failure_reason is not None:
            return path_result.failure_reason
    return "incomplete-evidence"


def _file_validation_result(
    validation_type: str,
    catalog_path: str,
    passed: bool,
    failure_reason: str | None,
    **details: object,
) -> QuestValidationResult:
    return QuestValidationResult(
        passed=passed,
        failure_reason=failure_reason,
        evidence=_validation_evidence(
            validation_type,
            passed,
            failure_reason,
            catalog_path=catalog_path,
            path_category=_validation_path_category(catalog_path),
            **details,
        ),
    )


def _validation_path_category(catalog_path: str) -> str:
    if catalog_path == "~" or catalog_path.startswith("~/"):
        return "learner-home"
    if Path(catalog_path).is_absolute():
        return "absolute"
    return "learner-relative"


def _validation_evidence(
    validation_type: str,
    passed: bool,
    failure_reason: str | None,
    **details: object,
) -> JsonPayload:
    return {
        "validation_type": validation_type,
        "passed": passed,
        "failure_reason": failure_reason,
        **details,
    }


def _unsupported_validation_types(validation: QuestValidation) -> frozenset[str]:
    if isinstance(validation, AllOfValidation):
        return frozenset(
            validation_type
            for child_validation in validation.validations
            for validation_type in _unsupported_validation_types(child_validation)
        )
    validation_type_id = _validation_type_id(validation)
    if validation_type_id in _SUPPORTED_VALIDATION_TYPE_IDS:
        return frozenset()
    return frozenset({validation_type_id})


def validation_answer_question(
    validation: QuestValidation | SessionObjectiveValidation,
) -> str | None:
    """Return the first learner-answer question in one validation tree."""
    match validation:
        case InteractiveQuestionValidation(question=question):
            return question
        case LearnerHandleQuestionValidation(question=question):
            return question
        case AllOfValidation(validations=validations):
            for child_validation in validations:
                if (question := validation_answer_question(child_validation)) is not None:
                    return question
            return None
        case _:
            return None


def _validation_type_id(validation: object) -> str:
    return _camel_case_to_snake_case(validation.__class__.__name__).removesuffix("_validation")


def _camel_case_to_snake_case(value: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).casefold()
