"""Create a learner account through infra helpers and initialize app state."""

from __future__ import annotations

import argparse
import pwd
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from rich.console import Console

from maker_guide.cli.registration import registration_is_open
from maker_guide.deployment import (
    CONFIGURATION_FILE,
    LLDAP_CREATE_USER_COMMAND,
    MAKER_GUIDE_DAEMON_USER,
    MAKER_GUIDE_INITIALIZE_LEARNER_COMMAND,
    REFRESH_LEARNER_ROUTES_COMMAND,
    REGISTRATION_STATE_FILE,
    RUN_USER_COMMAND,
)


@dataclass(frozen=True, kw_only=True, slots=True)
class CreateLearnerOptions:
    """Resolved options for one learner creation run."""

    registration_mode: bool
    resume: bool
    username: str
    email: str | None
    password_stdin: bool
    lldap_create_user_command: str
    initialize_learner_command: str
    configuration_file: str
    run_user_command: str
    run_user: str
    refresh_learner_routes_command: str


def main(arguments: Sequence[str] | None = None) -> int:
    """Create a learner account and initialize Maker Guide state."""
    parsed_arguments = parse_arguments(arguments)
    password = sys.stdin.read() if parsed_arguments.password_stdin else None
    if parsed_arguments.registration_mode and not registration_is_open(
        Path(REGISTRATION_STATE_FILE),
    ):
        Console(stderr=True).print("Registration is closed.")
        return 1
    if parsed_arguments.resume:
        try:
            user_id_number = pwd.getpwnam(parsed_arguments.username).pw_uid
        except KeyError:
            Console(stderr=True).print("Cannot resume: the POSIX account does not exist.")
            return 1
        account_created = False
    else:
        try:
            user_id_number = create_lldap_user(parsed_arguments, password)
        except subprocess.CalledProcessError as error:
            Console(stderr=True).print(_process_error_message(error))
            return 1
        account_created = True
    try:
        initialize_learner(parsed_arguments, user_id_number)
        refresh_learner_routes(parsed_arguments)
    except subprocess.CalledProcessError as error:
        if account_created:
            Console(stderr=True).print(
                " ".join(
                    (
                        "Account created but Maker Guide provisioning is incomplete.",
                        f"Rerun with --resume {parsed_arguments.username}.",
                    ),
                ),
            )
        Console(stderr=True).print(_process_error_message(error))
        return 1
    return 0


def parse_arguments(arguments: Sequence[str] | None = None) -> CreateLearnerOptions:
    """Parse CLI arguments into typed options."""
    command_arguments = list(sys.argv[1:] if arguments is None else arguments)
    parser = argparse.ArgumentParser(
        description="Create a Maker Guide learner through the generic LLDAP helper."
    )
    _ = parser.add_argument("--registration-mode", action="store_true")
    _ = parser.add_argument("--resume", action="store_true")
    _ = parser.add_argument("username")
    _ = parser.add_argument("--email")
    _ = parser.add_argument("--password-stdin", action="store_true")
    _ = parser.add_argument(
        "--lldap-create-user-command",
        default=LLDAP_CREATE_USER_COMMAND,
    )
    _ = parser.add_argument(
        "--initialize-learner-command",
        default=MAKER_GUIDE_INITIALIZE_LEARNER_COMMAND,
    )
    _ = parser.add_argument(
        "--config",
        dest="configuration_file",
        default=CONFIGURATION_FILE,
    )
    _ = parser.add_argument("--run-user-command", default=RUN_USER_COMMAND)
    _ = parser.add_argument("--run-user", default=MAKER_GUIDE_DAEMON_USER)
    _ = parser.add_argument(
        "--refresh-learner-routes-command",
        default=REFRESH_LEARNER_ROUTES_COMMAND,
    )
    namespace = parser.parse_args(command_arguments)
    resume = parsed_bool(namespace, "resume")
    email = parsed_optional_string(namespace, "email")
    if resume and parsed_bool(namespace, "registration_mode"):
        parser.error("--resume cannot be used with --registration-mode")
    if not resume and email is None:
        parser.error("--email is required unless --resume is used")
    if resume and parsed_bool(namespace, "password_stdin"):
        parser.error("--password-stdin cannot be used with --resume")
    if parsed_bool(namespace, "registration_mode") and command_arguments != [
        "--registration-mode",
        parsed_string(namespace, "username"),
        "--email",
        email,
        "--password-stdin",
    ]:
        parser.error("registration mode only accepts a username, email, and --password-stdin")
    return CreateLearnerOptions(
        registration_mode=parsed_bool(namespace, "registration_mode"),
        resume=resume,
        username=parsed_string(namespace, "username"),
        email=email,
        password_stdin=parsed_bool(namespace, "password_stdin"),
        lldap_create_user_command=parsed_string(namespace, "lldap_create_user_command"),
        initialize_learner_command=parsed_string(namespace, "initialize_learner_command"),
        configuration_file=parsed_string(namespace, "configuration_file"),
        run_user_command=parsed_string(namespace, "run_user_command"),
        run_user=parsed_string(namespace, "run_user"),
        refresh_learner_routes_command=parsed_string(namespace, "refresh_learner_routes_command"),
    )


def parsed_bool(parsed_arguments: argparse.Namespace, name: str) -> bool:
    """Return one boolean argument from an argparse namespace."""
    return cast("bool", getattr(parsed_arguments, name))


def parsed_string(parsed_arguments: argparse.Namespace, name: str) -> str:
    """Return one string argument from an argparse namespace."""
    return cast("str", getattr(parsed_arguments, name))


def parsed_optional_string(parsed_arguments: argparse.Namespace, name: str) -> str | None:
    """Return one optional string argument from an argparse namespace."""
    return cast("str | None", getattr(parsed_arguments, name))


def create_lldap_user(options: CreateLearnerOptions, password: str | None) -> int:
    """Create the generic LLDAP/POSIX account and return its assigned UID."""
    if options.email is None:
        raise ValueError("email is required to create an LLDAP account")
    command = [
        options.lldap_create_user_command,
        options.username,
        "--email",
        options.email,
        "--print-user-id-number",
    ]
    if options.password_stdin:
        command.append("--password-stdin")
    completed_process = subprocess.run(  # noqa: S603 - root wrapper command path is deployment-configured.
        command,
        check=True,
        input=password,
        stdout=subprocess.PIPE,
        text=True,
    )
    return int(completed_process.stdout.strip())


def initialize_learner(options: CreateLearnerOptions, user_id_number: int) -> None:
    """Initialize Maker Guide app state as the daemon user."""
    _ = subprocess.run(  # noqa: S603 - root wrapper command path is deployment-configured.
        [
            options.run_user_command,
            "-u",
            options.run_user,
            "--",
            options.initialize_learner_command,
            options.username,
            "--uid",
            str(user_id_number),
            "--config",
            options.configuration_file,
        ],
        check=True,
    )


def refresh_learner_routes(options: CreateLearnerOptions) -> None:
    """Regenerate and reload the root-owned learner route configuration."""
    _ = subprocess.run(  # noqa: S603 - root wrapper command path is deployment-configured.
        [options.refresh_learner_routes_command],
        check=True,
    )


def _process_error_message(error: subprocess.CalledProcessError) -> str:
    command = cast("Sequence[object]", error.cmd)
    command_text = " ".join(str(part) for part in command)
    return f"{command_text} failed with status {error.returncode}"
