"""Registration data models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True, slots=True)
class RegistrationOptions:
    """Configuration for one learner registration run."""

    create_user_command: str
    sudo_command: str
    getent_command: str
    pwscore_command: str
    logo_command: str
    fully_qualified_domain_name: str
    login_host: str
    web_ssh_url: str


@dataclass(frozen=True, kw_only=True, slots=True)
class RegistrationRequest:
    """Validated learner registration request."""

    username: str
    email: str | None
    passphrase: str
