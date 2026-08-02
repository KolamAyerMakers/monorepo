"""Command-line entry point for learner registration."""

from __future__ import annotations

import argparse
import logging
import socket
from collections.abc import Sequence
from logging.handlers import SysLogHandler
from typing import cast

from maker_guide.deployment import MAKER_GUIDE_CREATE_LEARNER_COMMAND
from maker_guide.registration.models import RegistrationOptions
from maker_guide.registration.service import default_runtime, run_main_loop


def main() -> int:
    """Run the learner registration command."""
    configure_logging()
    return run_main_loop(default_runtime(parse_arguments()))


def configure_logging() -> None:
    """Send registration lifecycle events to the system journal."""
    registration_logger = logging.getLogger("maker_guide.registration")
    registration_logger.setLevel(logging.INFO)
    syslog_handler = SysLogHandler(address="/dev/log", facility=SysLogHandler.LOG_AUTHPRIV)
    syslog_handler.ident = "maker-guide-registration: "
    registration_logger.addHandler(syslog_handler)


def parse_arguments(arguments: Sequence[str] | None = None) -> RegistrationOptions:
    """Parse command-line arguments into registration options."""
    argument_parser = argparse.ArgumentParser(
        description="Interactive Kolam Ayer Makers account registration.",
    )
    argument_parser.add_argument(
        "--create-user-command",
        default=MAKER_GUIDE_CREATE_LEARNER_COMMAND,
    )
    argument_parser.add_argument("--sudo-command", default="/usr/bin/sudo")
    argument_parser.add_argument("--getent-command", default="/usr/bin/getent")
    argument_parser.add_argument("--pwscore-command", default="/usr/bin/pwscore")
    argument_parser.add_argument("--logo-command", default="/usr/local/bin/kolam-makers-logo")
    argument_parser.add_argument(
        "--fully-qualified-domain-name",
        default=default_fully_qualified_domain_name(),
    )
    argument_parser.add_argument("--login-host", default=default_fully_qualified_domain_name())
    argument_parser.add_argument("--web-ssh-url", default="")
    parsed_arguments = argument_parser.parse_args(arguments)
    return RegistrationOptions(
        create_user_command=parsed_string(parsed_arguments, "create_user_command"),
        sudo_command=parsed_string(parsed_arguments, "sudo_command"),
        getent_command=parsed_string(parsed_arguments, "getent_command"),
        pwscore_command=parsed_string(parsed_arguments, "pwscore_command"),
        logo_command=parsed_string(parsed_arguments, "logo_command"),
        fully_qualified_domain_name=parsed_string(
            parsed_arguments,
            "fully_qualified_domain_name",
        ),
        login_host=parsed_string(parsed_arguments, "login_host"),
        web_ssh_url=parsed_string(parsed_arguments, "web_ssh_url"),
    )


def parsed_string(parsed_arguments: argparse.Namespace, name: str) -> str:
    """Return one string argument from an argparse namespace."""
    return cast("str", getattr(parsed_arguments, name))


def default_fully_qualified_domain_name() -> str:
    """Return the local fully qualified domain name with a safe fallback."""
    return socket.getfqdn().strip(".") or "localhost"


if __name__ == "__main__":
    raise SystemExit(main())
