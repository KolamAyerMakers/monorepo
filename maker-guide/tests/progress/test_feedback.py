"""Tests for learner-facing validation failure feedback."""

from __future__ import annotations

import pytest

from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.progress.feedback import failure_explanation, generic_failure_reason_coverage
from maker_guide.progress.validation import (
    GENERIC_VALIDATION_FAILURE_REASONS,
    validation_failure_reasons,
)


def test_generic_feedback_covers_every_generic_validation_reason() -> None:
    """Every generic validation reason can render safe learner-facing text."""
    assert generic_failure_reason_coverage() == GENERIC_VALIDATION_FAILURE_REASONS


@pytest.mark.parametrize(
    ("quest_id", "failure_reason", "expected_finding"),
    [
        (
            "prove-shell-alive",
            "missing-command",
            "I have not seen all three commands yet. Run `whoami`, `date`, and `uptime`.",
        ),
        (
            "name-system",
            "missing-concept",
            "Read `/etc/os-release` again and answer with the `PRETTY_NAME` value.",
        ),
        (
            "copy-and-inspect-ownership",
            "wrong-owner",
            (
                "Run `cp /etc/hostname ~/playground/hostname` yourself so your Unix account "
                "owns the copy."
            ),
        ),
        (
            "copy-and-inspect-ownership",
            "file-content-mismatch",
            ("Make `~/playground/hostname` an exact copy of `/etc/hostname`, then try again."),
        ),
        (
            "build-playground",
            "missing-path",
            (
                "I need to see `~/playground/one.txt`, `~/playground/two.txt`, "
                "and `~/playground/three.txt`."
            ),
        ),
        (
            "build-playground",
            "permission-denied",
            (
                "Allow the guide to traverse your home directory, then check again: "
                "run `chmod 711 ~`."
            ),
        ),
        (
            "edit-with-micro",
            "file-content-mismatch",
            "Open `~/playground/micro-note.txt` again and make the first line exact.",
        ),
        (
            "make-file-executable",
            "not-executable",
            (
                "Set the owner executable bit on the required script, then try again: "
                "`~/playground/run-me.sh` needs a Bash shebang and executable permission."
            ),
        ),
        (
            "enable-site-service",
            "port-content-mismatch",
            (
                "Update the service file with your computed port, then try again: "
                "`site.service` must use your computed port, be enabled, and answer a local curl."
            ),
        ),
    ],
)
def test_quest_failure_feedback_overrides_generic_finding(
    quest_id: str,
    failure_reason: str,
    expected_finding: str,
) -> None:
    """Exact catalog feedback is shown before generic fallback text."""
    explanation = failure_explanation(CATALOG.quest(quest_id), failure_reason)

    assert explanation.found == expected_finding


def test_missing_quest_failure_feedback_uses_generic_finding() -> None:
    """Generic fallback text still covers reasons missing from quest feedback."""
    explanation = failure_explanation(CATALOG.quest("prove-shell-alive"), "permission-denied")

    assert explanation.checked == "The required filesystem evidence for this quest."
    assert explanation.found == (
        "I could not traverse or read the required path with normal Unix permissions. "
        "Check directory execute bits and file read bits."
    )


def test_checker_configuration_failures_use_operator_fallback() -> None:
    """Catalog/runtime defects are not described as learner filesystem mistakes."""
    explanation = failure_explanation(CATALOG.quest("prove-shell-alive"), "invalid-regex")

    assert explanation.checked == "The automatic checker configuration for this quest."
    assert explanation.found == "This quest checker has an invalid regex. Tell an instructor."


def test_every_catalog_validation_failure_reason_renders_feedback() -> None:
    """Every catalog validation failure reason has non-empty learner-facing feedback."""
    for quest in CATALOG.course.quests:
        for failure_reason in validation_failure_reasons(quest.validation):
            explanation = failure_explanation(quest, failure_reason)

            assert explanation.checked.strip(), (quest.id, failure_reason)
            assert explanation.found.strip(), (quest.id, failure_reason)
