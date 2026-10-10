"""Deterministic quest validation."""

from __future__ import annotations

import hashlib
import html
import json
import math
import os
import re
import sqlite3
import stat
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import Path
from typing import cast, override

from maker_guide.curriculum.models import (
    AllOfValidation,
    AnswerConcept,
    AnswerConceptAssessment,
    ArtifactCheckValidation,
    CommandHistoryValidation,
    CourseCatalog,
    ExecutablePathValidation,
    FileCheckValidation,
    FileMatchesPathValidation,
    GitTrackedPathValidation,
    InteractiveQuestionValidation,
    IrcChannelJoinObservedValidation,
    IrcCtcpVersionValidation,
    LearnerHandleQuestionValidation,
    OwnedPathValidation,
    PathExistsValidation,
    Quest,
    QuestValidation,
    QuestValidationLeaf,
    ServiceLabValidation,
    SessionObjectiveValidation,
    SiteCheckValidation,
    SshPublicKeyObservedValidation,
    UserPortFileValidation,
)
from maker_guide.repositories.audit_event import AuditEvent, list_recent_audit_events_by_type
from maker_guide.repositories.command_observation import (
    CommandObservation,
    list_recent_command_observations,
)
from maker_guide.repositories.helpers import JsonPayload
from maker_guide.service_lab import ServiceLabReport
from maker_guide.site_check import (
    SITE_CHECK_CASES,
    SiteCheckError,
    SiteCheckReport,
    read_site_check_source,
    site_check_failure_messages,
)
from maker_guide.timer_check import TimerCheckReport
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
_MAX_DIAGNOSTIC_FILE_CHARS = 4_000


class _TodayLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.found = False

    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a" and any(
            name == "href" and value is not None and value.strip() in {"today.html", "./today.html"}
            for name, value in attrs
        ):
            self.found = True


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
        "site-check-required",
        "site-check-stale",
        "site-check-failed",
        "timer-check-required",
        "timer-check-stale",
        "timer-check-failed",
        "timer-check-unsupported-client",
        "timer-check-unsafe-user",
        "service-lab-required",
        "service-lab-unavailable",
        "service-lab-unrepaired",
        "service-lab-explanation-unavailable",
    },
)
"""Failure reasons with generic learner-facing fallback copy."""
_VALIDATION_FAILURE_REASONS_BY_ID = {
    "site_check": _PATH_RESOLUTION_FAILURE_REASONS
    | _FILE_READ_FAILURE_REASONS
    | frozenset({"site-check-required", "site-check-stale", "site-check-failed"}),
    "command_history": frozenset({"missing-command"}),
    "path_exists": _PATH_RESOLUTION_FAILURE_REASONS,
    "executable_path": _PATH_RESOLUTION_FAILURE_REASONS
    | frozenset({"not-regular-file", "not-executable", "wrong-owner"}),
    "owned_path": _PATH_RESOLUTION_FAILURE_REASONS | frozenset({"not-regular-file", "wrong-owner"}),
    "file_check": _PATH_RESOLUTION_FAILURE_REASONS
    | _FILE_READ_FAILURE_REASONS
    | frozenset({"file-content-mismatch", "forbidden-content-present", "invalid-regex"}),
    "artifact_check": _PATH_RESOLUTION_FAILURE_REASONS
    | _FILE_READ_FAILURE_REASONS
    | frozenset({"file-content-mismatch"}),
    "file_matches_path": _PATH_RESOLUTION_FAILURE_REASONS
    | _FILE_READ_FAILURE_REASONS
    | frozenset({"file-content-mismatch"}),
    "git_tracked_path": _PATH_RESOLUTION_FAILURE_REASONS
    | frozenset({"git-path-not-committed", "git-path-modified", "git-repository-error"}),
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
        "site_check",
        "service_lab",
        "path_exists",
        "executable_path",
        "owned_path",
        "file_check",
        "artifact_check",
        "file_matches_path",
        "git_tracked_path",
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
    site_check_report: SiteCheckReport | None = None
    """Prepared outcomes; validation itself never executes learner code."""
    site_check_failure_reason: str | None = None
    """Source or transport failure encountered before the progress transaction."""
    service_lab_report: ServiceLabReport | None = None
    """Fresh invocation report; stored progress is never a substitute for inspection."""
    timer_check_report: TimerCheckReport | None = None
    """Fresh timer state report; static unit contents alone are insufficient."""
    timer_check_failure_reason: str | None = None
    """Failure preparing the current timer observation."""
    timer_validation_time_us: int | None = None
    """Injectable current realtime sampled immediately before timer validation."""


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
    if isinstance(validation, ServiceLabValidation):
        return _validate_service_lab(validation_input, validation)
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


def _validate_service_lab(
    validation_input: QuestValidationInput,
    validation: ServiceLabValidation,
) -> QuestValidationResult:
    report = validation_input.service_lab_report
    if report is None:
        failure_reason = "service-lab-required"
    elif report.scenario != validation.scenario or report.error is not None:
        failure_reason = "service-lab-unavailable"
    elif not report.started:
        failure_reason = "service-lab-required"
    elif not report.healthy:
        failure_reason = "service-lab-unrepaired"
    elif (
        validation_input.answer_text
        and validation_input.answer_text.strip()
        and (
            len(validation_input.answer_concept_assessments)
            != len(validation.answer.required_concepts)
            or {assessment.concept_id for assessment in validation_input.answer_concept_assessments}
            != {concept.id for concept in validation.answer.required_concepts}
        )
    ):
        failure_reason = "service-lab-explanation-unavailable"
    else:
        answer_result = _validate_interactive_question(validation_input, validation.answer)
        return QuestValidationResult(
            passed=answer_result.passed,
            failure_reason=answer_result.failure_reason,
            evidence={**answer_result.evidence, "validation_type": "service_lab"},
        )
    return QuestValidationResult(
        passed=False,
        failure_reason=failure_reason,
        evidence=_validation_evidence("service_lab", False, failure_reason),
    )


def validation_support(validation: SessionObjectiveValidation) -> QuestValidationSupport:
    """Return runtime support status for a validation tree."""
    unsupported_validation_types = _unsupported_validation_types(validation)
    return QuestValidationSupport(
        supported=not unsupported_validation_types,
        unsupported_validation_types=tuple(sorted(unsupported_validation_types)),
    )


def validation_failure_reasons(validation: SessionObjectiveValidation) -> frozenset[str]:
    """Return stable failure reasons the runtime can emit for a validation tree."""
    if isinstance(validation, ServiceLabValidation):
        return validation_failure_reasons(validation.answer) | frozenset(
            {
                "service-lab-required",
                "service-lab-unavailable",
                "service-lab-unrepaired",
                "service-lab-explanation-unavailable",
                "contradicted-concept",
            }
        )
    if isinstance(validation, AllOfValidation):
        return frozenset(
            failure_reason
            for child_validation in validation.validations
            for failure_reason in validation_failure_reasons(child_validation)
        ) | frozenset({"incomplete-evidence"})
    if isinstance(validation, (FileCheckValidation, ArtifactCheckValidation)):
        validation_type = (
            "file_check" if isinstance(validation, FileCheckValidation) else "artifact_check"
        )
        failure_reasons = _VALIDATION_FAILURE_REASONS_BY_ID[validation_type]
        if isinstance(validation, FileCheckValidation) and validation.forbidden_regex is None:
            failure_reasons -= frozenset({"forbidden-content-present"})
        if isinstance(validation, ArtifactCheckValidation) and validation.kind == "timer":
            failure_reasons |= frozenset(
                {
                    "timer-check-required",
                    "timer-check-stale",
                    "timer-check-failed",
                    "timer-check-unsupported-client",
                    "timer-check-unsafe-user",
                }
            )
        return failure_reasons
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


def _validate_rule(  # noqa: C901, PLR0912 - exhaustive validation dispatch
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
        case ArtifactCheckValidation():
            result = _validate_artifact_check(validation_input, validation)
        case SiteCheckValidation():
            result = _validate_site_check(validation_input)
        case FileMatchesPathValidation():
            result = _validate_file_matches_path(validation_input, validation)
        case GitTrackedPathValidation():
            result = _validate_git_tracked_path(validation_input, validation)
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
    missing_pattern_indexes = tuple(
        index for index, observation in enumerate(matched_observations) if observation is None
    )
    passed = not missing_pattern_indexes
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
            missing_pattern_indexes=list(missing_pattern_indexes),
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
        matched=(
            semantic_assessment.verdict == "demonstrated"
            if semantic_assessment is not None
            else matched
        ),
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


def _validate_artifact_check(
    validation_input: QuestValidationInput,
    validation: ArtifactCheckValidation,
) -> QuestValidationResult:
    contents: list[str] = []
    for catalog_path in validation.paths:
        opened_file = open_validation_file(
            validation_input.handle,
            catalog_path,
            account_lookup=validation_input.account_lookup,
        )
        if opened_file.failure_reason is not None or opened_file.file_descriptor is None:
            return _file_validation_result(
                "artifact_check",
                catalog_path,
                False,
                opened_file.failure_reason or "read-error",
                artifact=validation.kind,
            )
        try:
            file_read = _read_validation_file(opened_file.file_descriptor)
        finally:
            os.close(opened_file.file_descriptor)
        if file_read.failure_reason is not None or file_read.file_contents is None:
            return _file_validation_result(
                "artifact_check",
                catalog_path,
                False,
                file_read.failure_reason or "read-error",
                artifact=validation.kind,
            )
        contents.append(file_read.file_contents)

    passed, failure_reason, artifact_issue = _artifact_content_result(validation.kind, contents)
    if validation.kind == "timer":
        runtime_failure = _timer_check_failure_reason(validation_input)
        if runtime_failure is not None:
            passed = False
            failure_reason = runtime_failure
        artifact_issue = (
            "The timer must be enabled, active, waiting, current, and have a future deadline."
            if runtime_failure is not None
            else ""
            if passed
            else artifact_issue
        )
    return _file_validation_result(
        "artifact_check",
        validation.paths[0],
        passed,
        failure_reason,
        artifact=validation.kind,
        checked_paths=list(validation.paths),
        artifact_issue=artifact_issue or None,
        **(
            {
                "service_sha256": report.service_sha256,
                "timer_sha256": report.timer_sha256,
                "timer_loaded": report.timer_loaded,
                "timer_enabled": report.timer_enabled,
                "timer_active": report.timer_active,
                "timer_substate": report.timer_substate,
                "timer_unit": report.timer_unit,
                "timer_no_reload": report.timer_no_reload,
                "service_loaded": report.service_loaded,
                "service_active": report.service_active,
                "service_no_reload": report.service_no_reload,
                "timer_next_elapse_us": report.next_elapse_us,
                "observed_realtime_us": report.observed_realtime_us,
            }
            if validation.kind == "timer"
            and (report := validation_input.timer_check_report) is not None
            else {}
        ),
    )


def _artifact_content_result(kind: str, contents: list[str]) -> tuple[bool, str | None, str]:
    artifact_issue = "The artifact fields, units, or snapshot values do not match the exercise."
    try:
        passed = artifact_contents_match(kind, contents)
    except json.JSONDecodeError:
        return (
            False,
            "file-content-mismatch",
            "The JSON artifact is malformed; inspect its saved response.",
        )
    except (ValueError, TypeError, KeyError, IndexError, OverflowError):
        return (
            False,
            "file-content-mismatch",
            "The JSON artifact is missing a required field or has an invalid field type.",
        )
    if passed:
        return True, None, ""
    if kind in {"bulletin", "published"}:
        report = contents[0] if kind == "bulletin" else contents[1]
        issues = _bulletin_issues(report)
        if kind == "published":
            issues.extend(_published_link_issues(contents[0], contents[2]))
        artifact_issue = "; ".join(issues)
    return False, "file-content-mismatch", artifact_issue


def _timer_check_failure_reason(validation_input: QuestValidationInput) -> str | None:
    if validation_input.timer_check_failure_reason is not None:
        return validation_input.timer_check_failure_reason
    report = validation_input.timer_check_report
    if report is None:
        return "timer-check-required"
    validation_time_us = validation_input.timer_validation_time_us
    if report.error is not None or not (
        report.timer_loaded
        and report.timer_enabled
        and report.timer_active
        and report.timer_substate == "waiting"
        and report.timer_unit == "site-build.service"
        and report.timer_no_reload
        and report.service_loaded
        and report.service_no_reload
        and 0 < report.next_elapse_us < 18_446_744_073_709_551_615
        and report.next_elapse_us > report.observed_realtime_us
        and validation_time_us is not None
        and 0 <= validation_time_us <= 18_446_744_073_709_551_615
        and report.next_elapse_us > validation_time_us
    ):
        return "timer-check-failed"
    return None


def artifact_contents_match(kind: str, contents: list[str]) -> bool:
    """Check learner artifacts against required JSON values and domain fields."""
    passed = False
    if kind == "weather":
        weather = _json_mapping(cast("object", json.loads(contents[0])))
        daily = _json_mapping(weather["daily"])
        forecast_date = _json_string(_json_first(daily["time"]))
        temperature = _json_number(_json_first(daily["temperature_2m_max"]))
        rain = _json_number(_json_first(daily["precipitation_probability_max"]))
        sunrise = _json_string(_json_first(daily["sunrise"]))
        sunset = _json_string(_json_first(daily["sunset"]))
        units = _json_mapping(weather["daily_units"])
        passed = (
            _valid_api_date(forecast_date)
            and _is_finite_number(temperature)
            and -100 <= temperature <= 70
            and _is_finite_number(rain)
            and 0 <= rain <= 100
            and all(_valid_api_timestamp(value) for value in (sunrise, sunset))
            and units["temperature_2m_max"] == "°C"
            and units["precipitation_probability_max"] == "%"
        )
    if kind == "temperature":
        weather = _json_mapping(cast("object", json.loads(contents[1])))
        number_text = contents[0].strip()
        daily = _json_mapping(weather["daily"])
        units = _json_mapping(weather["daily_units"])
        expected = _json_number(_json_first(daily["temperature_2m_max"]))
        passed = (
            _is_finite_number(expected)
            and units["temperature_2m_max"] == "°C"
            and re.fullmatch(r"-?\d+(?:\.\d+)?", number_text) is not None
            and Decimal(number_text) == Decimal(str(expected))
        )
    if kind == "air":
        air = _json_mapping(cast("object", json.loads(contents[0])))
        current = _json_mapping(air["current"])
        units = _json_mapping(air["current_units"])
        value = _json_number(current["pm2_5"])
        timestamp = _json_string(current["time"])
        passed = (
            _is_finite_number(value)
            and 0 <= value <= 1000
            and units["pm2_5"] == "μg/m³"
            and _valid_api_timestamp(timestamp)
            and _label_has_number(contents[1], r"PM2\.5", value, "μg/m³")
            and _label_has_text(
                contents[1], r"(?:air\s+)?model\s+timestamp|model\s+time|air\s+time", timestamp
            )
        )
    if kind == "forecast":
        weather = _json_mapping(cast("object", json.loads(contents[0])))
        daily = _json_mapping(weather["daily"])
        units = _json_mapping(weather["daily_units"])
        temperature = _json_number(_json_first(daily["temperature_2m_max"]))
        passed = (
            _is_finite_number(temperature)
            and units["temperature_2m_max"] == "°C"
            and re.search(r"(?m)^#\s+\S", contents[1]) is not None
            and _label_has_number(contents[1], r"maximum(?:\s+temperature)?", temperature, "°C")
        )
    if kind == "bulletin":
        passed = _report_has_complete_bulletin(contents[0])
    elif kind == "published":
        index, rendered_report, published_homepage = contents
        passed = _report_has_complete_bulletin(rendered_report) and not _published_link_issues(
            index, published_homepage
        )
    elif kind == "timer":
        service, timer = contents
        service_section = re.search(r"(?ms)^\[Service\]\n(?P<body>.*?)(?=^\[|\Z)", service)
        if service_section is not None:
            service_body = service_section["body"]
            prestart = re.search(
                r"(?m)^ExecStartPre=/bin/bash %h/scripts/today\.sh\s*$",
                service_body,
            )
            start = re.search(
                r"(?m)^ExecStart=/usr/local/bin/maker-guide-build-personal-website\s*$",
                service_body,
            )
            passed = (
                re.search(r"(?m)^Type=oneshot\s*$", service_body) is not None
                and re.search(r"(?m)^WorkingDirectory=%h/src\s*$", service_body) is not None
                and len(re.findall(r"(?m)^ExecStartPre=", service_body)) == 1
                and len(re.findall(r"(?m)^ExecStart=", service_body)) == 1
                and prestart is not None
                and start is not None
                and prestart.start() < start.start()
                and _valid_hourly_timer(timer)
            )
    return passed


def _json_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("expected a JSON object")
    mapping = cast("dict[object, object]", value)
    if not all(isinstance(key, str) for key in mapping):
        raise ValueError("JSON object keys must be strings")
    return cast("dict[str, object]", mapping)


def _json_first(value: object) -> object:
    if isinstance(value, list) and value:
        return cast("list[object]", value)[0]
    raise ValueError("expected a nonempty JSON array")


def _json_number(value: object) -> int | float:
    if _is_finite_number(value):
        return cast("int | float", value)
    raise ValueError("expected a finite JSON number")


def _json_string(value: object) -> str:
    if isinstance(value, str):
        return value
    raise ValueError("expected a JSON string")


def _is_finite_number(value: object) -> bool:
    return (isinstance(value, int) and not isinstance(value, bool)) or (
        isinstance(value, float) and math.isfinite(value)
    )


def _label_has_number(text: str, label: str, value: object, unit: str) -> bool:
    if not _is_finite_number(value):
        return False
    expected = Decimal(str(value))
    number_pattern = r"(?<![\w.,])(?P<number>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"
    unit_pattern = _unit_pattern(unit)
    for line in text.splitlines():
        label_match = re.search(rf"(?i)\b(?:{label})\b", line)
        if label_match is None:
            continue
        match = re.search(rf"{number_pattern}\s*{unit_pattern}(?!\w)", line[label_match.end() :])
        if match is not None:
            return Decimal(match["number"]) == expected
    return False


def _label_has_text(text: str, label: str, value: str) -> bool:
    return re.search(rf"(?im)^.*\b(?:{label})\b[^\n]*{re.escape(value)}", text) is not None


def _valid_hourly_timer(timer: str) -> bool:
    timer_section = re.search(r"(?ms)^\[Timer\]\n(?P<body>.*?)(?=^\[|\Z)", timer)
    if timer_section is None:
        return False
    body = timer_section["body"]
    outside_timer = timer[: timer_section.start()] + timer[timer_section.end() :]
    install_section = re.search(r"(?ms)^\[Install\]\n(?P<body>.*?)(?=^\[|\Z)", timer)
    return (
        install_section is not None
        and re.search(r"(?m)^WantedBy=timers\.target\s*$", install_section["body"]) is not None
        and len(re.findall(r"(?m)^OnCalendar=", timer)) == 1
        and len(re.findall(r"(?m)^OnCalendar=hourly\s*$", body)) == 1
        and len(re.findall(r"(?m)^RandomizedDelaySec=", timer)) == 1
        and len(re.findall(r"(?m)^RandomizedDelaySec=55min\s*$", body)) == 1
        and re.search(r"(?m)^RandomizedDelaySec=", outside_timer) is None
        and re.search(
            r"(?m)^On(?:BootSec|StartupSec|UnitActiveSec|ActiveSec|UnitInactiveSec)=", body
        )
        is None
        and re.search(
            r"(?m)^On(?:BootSec|StartupSec|UnitActiveSec|ActiveSec|UnitInactiveSec)=",
            outside_timer,
        )
        is None
    )


def _report_has_complete_bulletin(report: str) -> bool:
    return not _bulletin_issues(report)


def _bulletin_issues(report: str) -> list[str]:
    plain_report = html.unescape(
        re.sub(
            r"</(?:p|li|h[1-6]|tr|dt|dd|div)>|<br\s*/?>",
            "\n",
            report,
            flags=re.IGNORECASE,
        )
    )
    plain_report = re.sub(r"<[^>]*>|[*_`]", " ", plain_report)
    field_labels = r"""
        forecast\s+date|date|forecast\s+maximum(?:\s+temperature)?|temperature|time|
        daily\s+maximum(?:\s+temperature)?|maximum(?:\s+temperature)?|
        high(?:\s+temperature)?|rain(?:fall)?(?:\s+(?:probability|chance))?|
        precipitation(?:\s+probability)?|chance\s+of\s+rain|sunrise|sunset|
        (?:(?:modelled|modeled)\s+)?PM2\.5|(?:air\s+)?model\s+(?:timestamp|time)|
        (?:air\s+)?timestamp|retrieved|retrieval\s+time|generated(?:\s+at)?
    """
    plain_report = re.sub(
        rf"\b(?P<label>{field_labels})\s*:",
        r"\n\g<label>:",
        plain_report,
        flags=re.IGNORECASE | re.VERBOSE,
    )
    forecast_date = _labeled_field(plain_report, r"(?:forecast\s+)?date")
    temperature = _labeled_number(
        plain_report,
        r"(?:forecast\s+)?(?:maximum|daily\s+maximum)(?:\s+temperature)?|high(?:\s+temperature)?|temperature",
        "°C",
    )
    rain = _labeled_number(
        plain_report,
        r"rain(?:fall)?(?:\s+(?:probability|chance))?|precipitation(?:\s+probability)?|chance\s+of\s+rain",
        "%",
    )
    sunrise = _labeled_field(plain_report, r"sunrise")
    sunset = _labeled_field(plain_report, r"sunset")
    pm25 = _labeled_number(plain_report, r"(?:(?:modelled|modeled)\s+)?PM2\.5", "μg/m³")
    model_time = _labeled_field(
        plain_report,
        r"(?:air\s+)?model\s+(?:timestamp|time)|(?:air\s+)?timestamp|time",
    )
    retrieved = _labeled_field(plain_report, r"retrieved|retrieval\s+time|generated(?:\s+at)?")
    issues: list[str] = []
    for value, label in (
        (forecast_date, "Date"),
        (sunrise, "Sunrise"),
        (sunset, "Sunset"),
        (model_time, "Air-quality time"),
        (retrieved, "Retrieval time"),
    ):
        if value is None:
            issues.append(f"Missing {label}.")
    for value, label, names, unit in (
        (
            temperature,
            "Temperature",
            r"(?:forecast\s+)?(?:maximum|daily\s+maximum)(?:\s+temperature)?|high(?:\s+temperature)?|temperature",
            "°C",
        ),
        (
            rain,
            "Rain probability",
            r"rain(?:fall)?(?:\s+(?:probability|chance))?|precipitation(?:\s+probability)?|chance\s+of\s+rain",
            "%",
        ),
        (pm25, "PM2.5", r"(?:(?:modelled|modeled)\s+)?PM2\.5", "μg/m³"),
    ):
        if value is None:
            field = _labeled_field(plain_report, names)
            if field is not None and re.search(r"\d", field):
                issues.append(f"Add {unit} to {label}.")
            else:
                issues.append(f"Missing {label} ({unit}).")
    if "open-meteo" not in plain_report.casefold():
        issues.append("Name Open-Meteo as a source.")
    if "cams" not in plain_report.casefold():
        issues.append("Name CAMS as a source.")
    if issues:
        return issues
    forecast_date = cast("str", forecast_date)
    temperature = cast("str", temperature)
    rain = cast("str", rain)
    sunrise = cast("str", sunrise)
    sunset = cast("str", sunset)
    pm25 = cast("str", pm25)
    model_time = cast("str", model_time)
    retrieved = cast("str", retrieved)
    checks = (
        (_valid_api_date(forecast_date), "Date must be a real YYYY-MM-DD date."),
        (_within_range(temperature, -100, 70), "Temperature must be between -100 and 70 °C."),
        (_within_range(rain, 0, 100), "Rain probability must be between 0 and 100%."),
        (_valid_api_timestamp(sunrise), "Sunrise must be a valid ISO timestamp."),
        (_valid_api_timestamp(sunset), "Sunset must be a valid ISO timestamp."),
        (_within_range(pm25, 0, 1000), "PM2.5 must be between 0 and 1000 μg/m³."),
        (_valid_api_timestamp(model_time), "Air-quality time must be a valid ISO timestamp."),
        (_valid_retrieval_timestamp(retrieved), "Retrieval time must be a valid ISO timestamp."),
    )
    return [message for valid, message in checks if not valid]


def _within_range(value: str, minimum: int, maximum: int) -> bool:
    try:
        number = Decimal(value)
        return number.is_finite() and minimum <= number <= maximum
    except InvalidOperation:
        return False


def _published_link_issues(index: str, homepage: str) -> list[str]:
    issues: list[str] = []
    if re.search(r"\[[^\]]+\]\(today\.html\)", index, re.IGNORECASE) is None:
        issues.append("Link to today.html from the site index.")
    parser = _TodayLinkParser()
    parser.feed(homepage)
    if not parser.found:
        issues.append("Link to today.html from the published homepage.")
    return issues


def _labeled_field(text: str, label: str) -> str | None:
    for raw_line in text.splitlines():
        line = re.sub(r"^\s*(?:[-*+]\s+|\d+[.)]\s+|#+\s*)", "", raw_line)
        match = re.fullmatch(rf"\s*(?:{label})\s*:?\s*(\S(?:.*?\S)?)\s*", line, re.IGNORECASE)
        if match is not None:
            return match[1].strip()
    return None


def _labeled_number(text: str, label: str, unit: str) -> str | None:
    value = _labeled_field(text, label)
    if value is None:
        return None
    match = re.search(
        rf"(?<![\w.,])([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*{_unit_pattern(unit)}",
        value,
    )
    return match[1] if match is not None else None


def _unit_pattern(unit: str) -> str:
    return re.escape(unit).replace("μ", "[μµ]")


def _valid_retrieval_timestamp(value: str) -> bool:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:\d{2})?", value) is None:
        return False
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def _valid_api_timestamp(value: str) -> bool:
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", value) is not None


def _valid_api_date(value: str) -> bool:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        return False
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def _validate_site_check(validation_input: QuestValidationInput) -> QuestValidationResult:
    source_sha256: str | None = None
    failure_reason = validation_input.site_check_failure_reason
    try:
        source_sha256 = hashlib.sha256(
            read_site_check_source(
                validation_input.handle, account_lookup=validation_input.account_lookup
            )
        ).hexdigest()
    except SiteCheckError as error:
        failure_reason = failure_reason or str(error)
    report = validation_input.site_check_report
    cases = _site_check_cases(report)
    if failure_reason is None:
        if report is None:
            failure_reason = "site-check-required"
        elif cases is None:
            failure_reason = "site-check-failed"
        elif report.source_sha256 != source_sha256:
            failure_reason = "site-check-stale"
        elif report.error is not None or not all(case_result[1] for case_result in cases):
            failure_reason = "site-check-failed"
    return _file_validation_result(
        "site_check",
        "~/scripts/site-check.sh",
        failure_reason is None,
        failure_reason,
        source_sha256=(
            report.source_sha256 if report is not None and cases is not None else source_sha256
        ),
        cases=[{"id": case_id, "passed": passed} for case_id, passed in cases or ()],
        failed_cases=[case_id for case_id, passed in cases or () if not passed],
        failure_messages=(
            list(site_check_failure_messages(report))
            if report is not None and cases is not None and failure_reason == "site-check-failed"
            else []
        ),
    )


def _site_check_cases(report: object) -> tuple[tuple[str, bool], ...] | None:
    """Treat even typed reports as untrusted, retaining only the exact bounded case set."""
    if not isinstance(report, SiteCheckReport):
        return None
    raw_digest = cast("object", report.source_sha256)
    raw_error = cast("object", report.error)
    if (
        not isinstance(raw_digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", raw_digest) is None
        or (raw_error is not None and not isinstance(raw_error, str))
    ):
        return None
    raw_cases = cast("object", report.cases)
    if not isinstance(raw_cases, tuple) or len(cast("tuple[object, ...]", raw_cases)) != len(
        SITE_CHECK_CASES
    ):
        return None
    cases: dict[str, bool] = {}
    for item in cast("tuple[object, ...]", raw_cases):
        if not isinstance(item, tuple) or len(cast("tuple[object, ...]", item)) != 2:
            return None
        case_id, passed = cast("tuple[object, object]", item)
        if (
            not isinstance(case_id, str)
            or case_id not in SITE_CHECK_CASES
            or case_id in cases
            or not isinstance(passed, bool)
        ):
            return None
        cases[case_id] = passed
    return tuple((case_id, cases[case_id]) for case_id in SITE_CHECK_CASES)


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


def _validate_git_tracked_path(
    validation_input: QuestValidationInput,
    validation: GitTrackedPathValidation,
) -> QuestValidationResult:
    resolution = resolve_validation_path(
        validation_input.handle,
        validation.repository_path,
        account_lookup=validation_input.account_lookup,
    )
    if resolution.failure_reason is not None or resolution.target_path is None:
        return _git_tracked_path_result(
            validation,
            False,
            resolution.failure_reason or "read-error",
        )
    command_prefix = (
        "git",
        "-c",
        f"safe.directory={resolution.target_path}",
        "-C",
        str(resolution.target_path),
    )
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    try:
        committed_path = subprocess.run(  # noqa: S603, catalog paths are validated and shell-free.
            (*command_prefix, "cat-file", "-e", f"HEAD:{validation.path}"),
            capture_output=True,
            check=False,
            timeout=5,
            env=environment,
        )
        if committed_path.returncode != 0:
            return _git_tracked_path_result(validation, False, "git-path-not-committed")
        clean_path = subprocess.run(  # noqa: S603, catalog paths are validated and shell-free.
            (*command_prefix, "diff", "--quiet", "HEAD", "--", validation.path),
            capture_output=True,
            check=False,
            timeout=5,
            env=environment,
        )
    except (OSError, subprocess.TimeoutExpired):
        return _git_tracked_path_result(validation, False, "git-repository-error")
    if clean_path.returncode == 0:
        return _git_tracked_path_result(validation, True, None)
    if clean_path.returncode == 1:
        return _git_tracked_path_result(validation, False, "git-path-modified")
    return _git_tracked_path_result(validation, False, "git-repository-error")


def _git_tracked_path_result(
    validation: GitTrackedPathValidation,
    passed: bool,
    failure_reason: str | None,
) -> QuestValidationResult:
    return QuestValidationResult(
        passed=passed,
        failure_reason=failure_reason,
        evidence=_validation_evidence(
            "git_tracked_path",
            passed,
            failure_reason,
            repository_path=validation.repository_path,
            path=validation.path,
        ),
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
            content_excerpt=file_contents[:_MAX_DIAGNOSTIC_FILE_CHARS],
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
            content_excerpt=file_contents[:_MAX_DIAGNOSTIC_FILE_CHARS],
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


def _unsupported_validation_types(validation: SessionObjectiveValidation) -> frozenset[str]:
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
        case ServiceLabValidation(answer=answer):
            return answer.question
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
