"""Learner-facing explanations for deterministic validation failures."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import cast

from maker_guide.curriculum.models import Quest
from maker_guide.progress.validation import (
    GENERIC_VALIDATION_FAILURE_REASONS,
    QuestValidationResult,
)

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
        "site-check-required": "Simulated behavior of ~/scripts/site-check.sh.",
        "site-check-stale": "The script digest bound to the simulated checks.",
        "site-check-failed": "The seven simulated site-check outcomes.",
        "service-lab-required": "A started troubleshooting challenge and fresh local inspection.",
        "service-lab-unavailable": "Fresh diagnostic evidence for the current challenge.",
        "service-lab-unrepaired": "The service and page after your repair.",
        "service-lab-explanation-unavailable": "Assessment of your cause-and-repair explanation.",
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
        "site-check-required": (
            "`~/scripts/site-check.sh` needs simulated checks. Run `guide now` or `guide check` "
            "in the classroom shell; IRC cannot run local checks."
        ),
        "site-check-stale": (
            "`~/scripts/site-check.sh` changed during the check. Run `guide now` or `guide check` "
            "again in the classroom shell."
        ),
        "site-check-failed": (
            "`~/scripts/site-check.sh` has not passed all simulated cases. "
            "Run `guide now` or `guide check` again in the classroom shell."
        ),
        "service-lab-required": (
            "Run `guide now` in your SSH shell to start or inspect the challenge."
        ),
        "service-lab-unavailable": "The local inspection could not finish. Run `guide now` again.",
        "service-lab-unrepaired": (
            "The site is not repaired yet. Read the status, journal, and page."
        ),
        "service-lab-explanation-unavailable": (
            "Your site works again, but I couldn't assess your explanation. "
            "Please submit it again shortly; ask for help if this persists."
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


def site_check_feedback(validation_result: QuestValidationResult) -> str | None:
    """Share safe case-specific feedback between objective and quest presentation."""
    if validation_result.failure_reason not in {
        "site-check-required",
        "site-check-stale",
        "site-check-failed",
    }:
        return None
    messages = validation_result.evidence.get("failure_messages")
    next_step = (
        next(
            (
                message
                for message in cast("list[object]", messages)
                if isinstance(message, str) and message.strip()
            ),
            None,
        )
        if isinstance(messages, list)
        else None
    )
    if next_step is not None:
        response_parts = [
            "Your script ran locally against simulated responses, not your live website."
        ]
        cases = validation_result.evidence.get("cases")
        if isinstance(cases, list) and any(
            isinstance(case, dict)
            and cast("dict[str, object]", case).get("id") == "both-ok"
            and cast("dict[str, object]", case).get("passed") is True
            for case in cast("list[object]", cases)
        ):
            response_parts.append(
                "Passed: your script handles the homepage and report both returning HTTP 200."
            )
        response_parts.extend(
            (f"Next step: {next_step}", "Then run `guide now` again in the classroom shell.")
        )
        return "\n\n".join(response_parts)
    return _fallback_finding(validation_result.failure_reason)


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
