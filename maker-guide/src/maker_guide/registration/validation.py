"""Registration validation rules."""

from __future__ import annotations

import re

from maker_guide.identity.policy import HANDLE_PATTERN

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSPHRASE_EXAMPLES = (
    "orbit maple ceramic rain violet",
    "lantern-paper-quiet-signal-harbor",
    "four private words plus one sentence only you know",
)


def username_validation_error(username: str) -> str | None:
    """Return a learner-facing validation error for an invalid username."""
    if not username:
        return "Choose a username before continuing."
    if not HANDLE_PATTERN.fullmatch(username):
        return (
            "Use 2 to 32 characters: lowercase letters, numbers, and hyphens. Start with a letter."
        )
    if username.endswith("-"):
        return "Do not end the username with a hyphen."
    if "--" in username:
        return "Do not use repeated hyphens."
    return None


def email_validation_error(email: str) -> str | None:
    """Return a learner-facing validation error for an invalid email address."""
    if not email:
        return None
    if EMAIL_PATTERN.fullmatch(email):
        return None
    return "That does not look like an email address."


def local_passphrase_validation_error(username: str, passphrase: str) -> str | None:
    """Return a local passphrase validation error before invoking system policy."""
    if not passphrase:
        return "The passphrase is empty."
    if passphrase.strip().lower() in PASSPHRASE_EXAMPLES:
        return "Do not use one of the examples. Make your own passphrase."
    if username in passphrase.lower():
        return "It contains your username."
    return None
