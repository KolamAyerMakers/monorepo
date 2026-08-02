"""Learner registration workflow."""

from __future__ import annotations

import getpass
import logging
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass

from rich.console import Console

from maker_guide.registration.models import RegistrationOptions, RegistrationRequest
from maker_guide.registration.validation import (
    PASSPHRASE_EXAMPLES,
    email_validation_error,
    local_passphrase_validation_error,
    username_validation_error,
)

LOGGER = logging.getLogger(__name__)


class RegistrationError(Exception):
    """Raised when registration cannot complete."""


class QuitRegistrationError(Exception):
    """Raised when the learner cancels registration."""


@dataclass(frozen=True, kw_only=True, slots=True)
class RegistrationRuntime:
    """Runtime dependencies for an interactive registration run."""

    options: RegistrationOptions
    console: Console
    input_line: Callable[[str], str]
    input_secret: Callable[[str], str]
    environment: dict[str, str]


def run_registration(registration_runtime: RegistrationRuntime) -> str:
    """Run registration and return the created username."""
    show_logo(registration_runtime.options.logo_command)
    print_line(
        registration_runtime,
        "Welcome to the Kolam Ayer Makers server.",
        "bold cyan",
    )
    print_line(
        registration_runtime,
        "You are going to create your own personal user account.",
        "dim",
    )
    registration_request = RegistrationRequest(
        email=prompt_email(registration_runtime),
        username=prompt_username(registration_runtime),
        passphrase="",
    )
    registration_request = RegistrationRequest(
        email=registration_request.email,
        username=registration_request.username,
        passphrase=prompt_passphrase(registration_runtime, registration_request.username),
    )
    print_line(registration_runtime)
    print_line(registration_runtime, "Step 4: create account", "bold cyan")
    print_line(
        registration_runtime,
        "Creating the account now. This should only take a moment.",
        "dim",
    )
    create_user(registration_runtime.options, registration_request)
    return registration_request.username


def print_line(
    registration_runtime: RegistrationRuntime,
    text: str = "",
    style: str | None = None,
) -> None:
    """Write one styled line to the registration console."""
    registration_runtime.console.print(text, style=style, markup=False)


def prompt_line(registration_runtime: RegistrationRuntime, prompt: str) -> str:
    """Read one stripped learner input line."""
    try:
        return registration_runtime.input_line(prompt).strip()
    except KeyboardInterrupt as error:
        raise QuitRegistrationError from error
    except EOFError as error:
        raise QuitRegistrationError from error


def prompt_secret(registration_runtime: RegistrationRuntime, prompt: str) -> str:
    """Read one learner secret input value."""
    try:
        return registration_runtime.input_secret(prompt)
    except KeyboardInterrupt as error:
        raise QuitRegistrationError from error
    except EOFError as error:
        raise QuitRegistrationError from error


def prompt_email(registration_runtime: RegistrationRuntime) -> str | None:
    """Prompt for an optional learner email address."""
    print_line(registration_runtime)
    print_line(registration_runtime, "Step 1: contact", "bold cyan")
    print_line(
        registration_runtime,
        "{} {}".format(
            "Email is optional. Add it if you want Kolam Ayer Makers systems to reach you",
            "later, or press Enter to skip for now.",
        ),
        "dim",
    )
    while True:
        email = prompt_line(
            registration_runtime,
            "email > ",
        )
        validation_error = email_validation_error(email)
        if validation_error is None:
            return email or None
        print_line(registration_runtime, validation_error, "yellow")


def prompt_username(registration_runtime: RegistrationRuntime) -> str:
    """Prompt for an available learner handle."""
    print_line(registration_runtime)
    print_line(registration_runtime, "Step 2: choose your handle", "bold cyan")
    print_line(
        registration_runtime,
        "{} {}".format(
            "Your username is your Kolam Ayer Makers identity: shell login, IRC nickname,",
            "Git name, and the label people will use when they work with you.",
        ),
        "dim",
    )
    print_line(
        registration_runtime,
        "Pick something short, readable, and still-you next month.",
        "dim",
    )
    while True:
        username = prompt_line(
            registration_runtime,
            "username > ",
        )
        validation_error = username_validation_error(username)
        if validation_error is not None:
            print_line(registration_runtime, validation_error, "yellow")
            continue
        if is_username_available(registration_runtime.options.getent_command, username):
            print_line(registration_runtime, f"Available: {username}", "green")
            return username
        print_line(registration_runtime, f"Taken: {username}. Try another one.", "yellow")


def prompt_passphrase(registration_runtime: RegistrationRuntime, username: str) -> str:
    """Prompt for a strong confirmed passphrase."""
    print_line(registration_runtime)
    print_line(registration_runtime, "Step 3: build a passphrase", "bold cyan")
    print_line(
        registration_runtime,
        "{} {}".format(
            "This locks your account. Make it long enough to survive guesses, but memorable",
            "enough that you can actually type it tomorrow.",
        ),
        "dim",
    )
    print_line(
        registration_runtime,
        "When you type it, nothing will appear: no dots, no stars. That is normal.",
        "yellow",
    )
    print_line(registration_runtime, "Good patterns:", "bold cyan")
    for example in PASSPHRASE_EXAMPLES:
        print_line(registration_runtime, f"  {example}", "dim")
    while True:
        passphrase = prompt_secret(
            registration_runtime,
            "passphrase > ",
        )
        validation_error = passphrase_strength_error(
            registration_runtime.options.pwscore_command,
            username,
            passphrase,
        )
        if validation_error is not None:
            print_line(registration_runtime, f"Not strong enough: {validation_error}", "yellow")
            continue
        if prompt_secret(registration_runtime, "again > ") == passphrase:
            print_line(registration_runtime, "Passphrase accepted.", "green")
            return passphrase
        print_line(
            registration_runtime,
            "Those did not match. Re-enter the passphrase.",
            "yellow",
        )


def is_username_available(getent_command: str, username: str) -> bool:
    """Return whether the local account database has no matching username."""
    completed_process = subprocess.run(  # noqa: S603 - command path is deployment-configured.
        [getent_command, "passwd", username],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed_process.returncode == 0:
        return False
    if completed_process.returncode == 2:
        return True
    raise RegistrationError(
        completed_process.stderr.strip()
        or f"{getent_command} failed with status {completed_process.returncode}",
    )


def passphrase_strength_error(pwscore_command: str, username: str, passphrase: str) -> str | None:
    """Return a learner-facing passphrase strength error."""
    validation_error = local_passphrase_validation_error(username, passphrase)
    if validation_error is not None:
        return validation_error
    completed_process = subprocess.run(  # noqa: S603 - command path is deployment-configured.
        [pwscore_command],
        check=False,
        input=passphrase + "\n",
        capture_output=True,
        text=True,
    )
    if completed_process.returncode == 0:
        return None
    return (
        completed_process.stderr.strip()
        or completed_process.stdout.strip()
        or "The passphrase did not pass the system strength policy."
    )


def create_user(options: RegistrationOptions, registration_request: RegistrationRequest) -> None:
    """Create a learner account through the configured privileged helper."""
    completed_process = subprocess.run(  # noqa: S603 - command path is deployment-configured.
        create_user_command(options, registration_request),
        check=False,
        input=registration_request.passphrase + "\n",
        capture_output=True,
        text=True,
    )
    if completed_process.returncode == 0:
        return
    raise RegistrationError(
        completed_process.stderr.strip()
        or completed_process.stdout.strip()
        or f"{options.create_user_command} failed with status {completed_process.returncode}",
    )


def create_user_command(
    options: RegistrationOptions,
    registration_request: RegistrationRequest,
) -> list[str]:
    """Build the privileged learner creation command."""
    return [
        options.sudo_command,
        "-n",
        options.create_user_command,
        "--registration-mode",
        registration_request.username,
        "--email",
        registration_request.email
        or f"{registration_request.username}@{options.fully_qualified_domain_name}",
        "--password-stdin",
    ]


def show_logo(logo_command: str) -> None:
    """Display the server logo when the optional command exists."""
    try:
        subprocess.run([logo_command], check=False)  # noqa: S603 - optional configured logo.
    except FileNotFoundError:
        return


def prompt_restart_or_quit(registration_runtime: RegistrationRuntime) -> bool:
    """Prompt whether a failed registration should restart."""
    while True:
        answer = prompt_line(
            registration_runtime,
            "restart or quit? [r/q] > ",
        ).lower()
        if answer in {"r", "restart"}:
            return True
        if answer in {"q", "quit"}:
            return False
        print_line(registration_runtime, "Type 'r' to restart or 'q' to quit.", "yellow")


def prompt_close_session(registration_runtime: RegistrationRuntime) -> None:
    """Prompt before closing the registration session."""
    try:
        prompt_line(
            registration_runtime,
            "Press Enter to close this SSH session. ",
        )
    except QuitRegistrationError:
        print_line(registration_runtime)


def print_success_message(registration_runtime: RegistrationRuntime, username: str) -> None:
    """Print learner-facing instructions after successful registration."""
    print_line(registration_runtime)
    print_line(registration_runtime, "Registration successful.", "bold green")
    print_line(
        registration_runtime,
        "{} {}".format(
            "Your account is ready. Disconnect now, then log in with",
            f"'ssh {username}@{registration_runtime.options.login_host}' and your new passphrase.",
        ),
        "green",
    )
    if registration_runtime.options.web_ssh_url:
        print_line(
            registration_runtime,
            "{} {} {}".format(
                "Or open",
                registration_runtime.options.web_ssh_url,
                f"and sign in as '{username}' with your new passphrase.",
            ),
            "green",
        )


def run_main_loop(registration_runtime: RegistrationRuntime) -> int:
    """Run registration and return a process exit status."""
    while True:
        try:
            username = run_registration(registration_runtime)
        except (KeyboardInterrupt, QuitRegistrationError):
            LOGGER.warning("Registration cancelled.")
            print_line(registration_runtime)
            print_line(registration_runtime, "Registration cancelled.", "yellow")
            return 130
        except RegistrationError as error:
            LOGGER.error("Registration failed: %s", error)
            print_line(registration_runtime)
            print_line(registration_runtime, f"Account creation failed: {error}", "red")
            try:
                restart_registration = prompt_restart_or_quit(registration_runtime)
            except QuitRegistrationError:
                LOGGER.warning("Registration cancelled.")
                print_line(registration_runtime)
                print_line(registration_runtime, "Registration cancelled.", "yellow")
                return 130
            if restart_registration:
                print_line(registration_runtime)
                continue
            return 1
        LOGGER.info("Registration completed for username %s.", username)
        print_success_message(registration_runtime, username)
        prompt_close_session(registration_runtime)
        return 0


def default_runtime(options: RegistrationOptions) -> RegistrationRuntime:
    """Build runtime dependencies for normal command-line execution."""
    return RegistrationRuntime(
        options=options,
        console=Console(file=sys.stdout),
        input_line=input,
        input_secret=getpass.getpass,
        environment=dict(os.environ),
    )
