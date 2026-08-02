"""Tests for learner registration validation."""

from __future__ import annotations

import pytest

from maker_guide.registration.validation import (
    PASSPHRASE_EXAMPLES,
    email_validation_error,
    local_passphrase_validation_error,
    username_validation_error,
)

USERNAME_PATTERN_ERROR = (
    "Use 2 to 32 characters: lowercase letters, numbers, and hyphens. Start with a letter."
)


@pytest.mark.parametrize(
    "username",
    ["ab", "alice", "alice-1", "a" * 32],
)
def test_username_validation_accepts_valid_handles(username: str) -> None:
    """Valid learner handles pass validation."""
    assert username_validation_error(username) is None


@pytest.mark.parametrize(
    ("username", "expected_error"),
    [
        ("", "Choose a username before continuing."),
        ("a", USERNAME_PATTERN_ERROR),
        ("1alice", USERNAME_PATTERN_ERROR),
        ("Alice", USERNAME_PATTERN_ERROR),
        ("a" * 33, USERNAME_PATTERN_ERROR),
        ("alice-", "Do not end the username with a hyphen."),
        ("alice--bob", "Do not use repeated hyphens."),
    ],
)
def test_username_validation_rejects_invalid_handles(
    username: str,
    expected_error: str,
) -> None:
    """Invalid learner handles return the expected learner-facing reason."""
    assert username_validation_error(username) == expected_error


@pytest.mark.parametrize("email", ["", "alice@example.test", "a@b.co"])
def test_email_validation_accepts_empty_or_valid_email(email: str) -> None:
    """Optional or valid email input passes validation."""
    assert email_validation_error(email) is None


@pytest.mark.parametrize("email", ["alice", "alice@", "alice example@test"])
def test_email_validation_rejects_invalid_email(email: str) -> None:
    """Invalid email input returns the expected learner-facing reason."""
    assert email_validation_error(email) == "That does not look like an email address."


@pytest.mark.parametrize(
    ("username", "passphrase", "expected_error"),
    [
        ("alice", "", "The passphrase is empty."),
        ("alice", "alice has a long passphrase", "It contains your username."),
    ],
)
def test_local_passphrase_validation_rejects_obvious_failures(
    username: str,
    passphrase: str,
    expected_error: str,
) -> None:
    """Local passphrase checks reject empty or username-derived phrases."""
    assert local_passphrase_validation_error(username, passphrase) == expected_error


def test_local_passphrase_validation_accepts_non_empty_private_phrase() -> None:
    """A non-empty passphrase that omits the username passes local checks."""
    assert local_passphrase_validation_error("alice", "private comet window river signal") is None


@pytest.mark.parametrize("passphrase", PASSPHRASE_EXAMPLES)
def test_local_passphrase_validation_rejects_examples(passphrase: str) -> None:
    """Displayed example passphrases cannot be reused by learners."""
    assert (
        local_passphrase_validation_error("alice", passphrase)
        == "Do not use one of the examples. Make your own passphrase."
    )
