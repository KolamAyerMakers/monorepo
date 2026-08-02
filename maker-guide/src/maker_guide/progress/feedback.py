"""Learner-facing explanations for deterministic validation failures."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from maker_guide.curriculum.models import Quest
from maker_guide.progress.validation import GENERIC_VALIDATION_FAILURE_REASONS

_DEFAULT_CHECK_DESCRIPTION = "The latest deterministic validation attempt."
_DEFAULT_FAILURE_FINDING = "The available evidence is not enough to complete the quest."
_FILESYSTEM_EVIDENCE_CHECK_DESCRIPTION = "The required filesystem evidence for this quest."
_FILESYSTEM_ARTIFACT_CHECK_DESCRIPTION = (
    "The required file, directory, content, or executable bit for this quest."
)
_CHECK_DESCRIPTIONS = MappingProxyType(
    {
        "missing-command": "Recent successful command evidence for this quest.",
        "missing-answer": "The answer required for this quest.",
        "missing-concept": "The required concepts in your answer for this quest.",
        "contradicted-concept": "The required concepts in your answer for this quest.",
        "wrong-owner": "The required file ownership for this quest.",
        "wrong-answer": "The owner answer required for this quest.",
        "unsupported-validation": "Whether this quest has an automatic checker available.",
        "incomplete-evidence": "All deterministic validation checks required by this quest.",
        "missing-path": _FILESYSTEM_ARTIFACT_CHECK_DESCRIPTION,
        "not-regular-file": _FILESYSTEM_ARTIFACT_CHECK_DESCRIPTION,
        "not-executable": _FILESYSTEM_ARTIFACT_CHECK_DESCRIPTION,
        "file-content-mismatch": _FILESYSTEM_ARTIFACT_CHECK_DESCRIPTION,
        "forbidden-content-present": _FILESYSTEM_ARTIFACT_CHECK_DESCRIPTION,
        "port-content-mismatch": _FILESYSTEM_ARTIFACT_CHECK_DESCRIPTION,
        "unknown-user": _FILESYSTEM_EVIDENCE_CHECK_DESCRIPTION,
        "unsafe-path": _FILESYSTEM_EVIDENCE_CHECK_DESCRIPTION,
        "path-escapes-scope": _FILESYSTEM_EVIDENCE_CHECK_DESCRIPTION,
        "broken-symlink": _FILESYSTEM_EVIDENCE_CHECK_DESCRIPTION,
        "symlink-loop": _FILESYSTEM_EVIDENCE_CHECK_DESCRIPTION,
        "permission-denied": _FILESYSTEM_EVIDENCE_CHECK_DESCRIPTION,
        "read-error": _FILESYSTEM_EVIDENCE_CHECK_DESCRIPTION,
        "file-too-large": _FILESYSTEM_EVIDENCE_CHECK_DESCRIPTION,
        "file-decode-error": _FILESYSTEM_EVIDENCE_CHECK_DESCRIPTION,
        "invalid-regex": "The automatic checker configuration for this quest.",
        "unsupported-port-formula": "The automatic checker configuration for this quest.",
        "missing-irc-ctcp-version": "The terminal IRC client evidence for this quest.",
        "unsupported-irc-client": "The terminal IRC client evidence for this quest.",
    },
)
_FALLBACK_FAILURE_FINDINGS = MappingProxyType(
    {
        "incomplete-evidence": "One or more required checks have not passed yet.",
        "missing-command": "Some required command evidence is still missing.",
        "missing-answer": "Use `guide answer 'your answer'` so I can check this quest.",
        "missing-concept": "Your answer is missing one or more required ideas.",
        "contradicted-concept": "Your answer says something that contradicts a required idea.",
        "wrong-owner": "The required file is not owned by your Unix account.",
        "wrong-answer": "Run `ls -l` on the required file and answer with its owner name.",
        "unsupported-validation": "This quest is not automatically checkable by the bot yet.",
        "unknown-user": "I could not find your Unix account for filesystem validation.",
        "unsafe-path": "A validation path is unsafe for automatic checking.",
        "path-escapes-scope": "A validation path escapes the allowed learner-home scope.",
        "missing-path": "A required file or directory does not exist yet.",
        "broken-symlink": "A required symlink points to a missing target.",
        "symlink-loop": "A required symlink loops instead of resolving to a real target.",
        "permission-denied": (
            "I could not traverse or read the required path with normal Unix permissions. "
            "Check directory execute bits and file read bits."
        ),
        "not-regular-file": "A required file check points at something that is not a regular file.",
        "not-executable": "A required script or program is missing the owner executable bit.",
        "read-error": "I could not read the required filesystem evidence.",
        "file-too-large": "A required file is too large for this deterministic check.",
        "file-decode-error": "A required file is not valid UTF-8 text.",
        "file-content-mismatch": (
            "A required file exists, but its contents do not match the quest requirement."
        ),
        "forbidden-content-present": "A required file still contains content this quest forbids.",
        "invalid-regex": "This quest checker has an invalid regex. Tell an instructor.",
        "port-content-mismatch": (
            "A required service file does not contain the expected learner-specific port."
        ),
        "unsupported-port-formula": (
            "This quest checker has an unsupported port formula. Tell an instructor."
        ),
        "missing-irc-ctcp-version": (
            "I have not verified your terminal IRC client yet. Message the guide from WeeChat."
        ),
        "unsupported-irc-client": (
            "The IRC client I saw is not accepted for this quest. Use WeeChat."
        ),
    },
)


@dataclass(frozen=True, kw_only=True, slots=True)
class FailureExplanation:
    """Safe text explaining one failed deterministic validation attempt."""

    checked: str
    """What the bot checked."""
    found: str
    """What the bot found or what the learner should try next."""


def failure_explanation(quest: Quest, failure_reason: str | None) -> FailureExplanation:
    """Return exact quest feedback first, then generic safe fallback copy."""
    return FailureExplanation(
        checked=_check_description(failure_reason),
        found=_quest_feedback_text(quest, failure_reason) or _fallback_finding(failure_reason),
    )


def generic_failure_reason_coverage() -> frozenset[str]:
    """Return generic validation reasons that have complete fallback explanations."""
    return frozenset(_CHECK_DESCRIPTIONS) & frozenset(_FALLBACK_FAILURE_FINDINGS)


def _check_description(failure_reason: str | None) -> str:
    if failure_reason is None:
        return _DEFAULT_CHECK_DESCRIPTION
    return _CHECK_DESCRIPTIONS.get(failure_reason, _DEFAULT_CHECK_DESCRIPTION)


def _quest_feedback_text(quest: Quest, failure_reason: str | None) -> str | None:
    if failure_reason is None:
        return None
    for feedback in quest.failure_feedback:
        if feedback.reason == failure_reason:
            return feedback.text
    return None


def _fallback_finding(failure_reason: str | None) -> str:
    if failure_reason is None:
        return _DEFAULT_FAILURE_FINDING
    return _FALLBACK_FAILURE_FINDINGS.get(failure_reason, _DEFAULT_FAILURE_FINDING)


if generic_failure_reason_coverage() != GENERIC_VALIDATION_FAILURE_REASONS:
    missing_reasons = GENERIC_VALIDATION_FAILURE_REASONS - generic_failure_reason_coverage()
    raise RuntimeError(f"missing generic validation feedback: {sorted(missing_reasons)}")
