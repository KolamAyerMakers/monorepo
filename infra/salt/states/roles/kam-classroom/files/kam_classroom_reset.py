#!/usr/bin/env python3
"""Remove one learner or reset all classroom runtime data."""

from __future__ import annotations

import argparse
import grp
import os
import pwd
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from collections.abc import Iterable
from pathlib import Path

CONFIRM_ALL = "RESET-LEARNING-ENVIRONMENT"
DATABASE_PATH = Path("/var/lib/maker-guide/state.db")
AUDIT_ROOT = Path("/var/lib/maker-guide/audit")
MAKERS_ROOT = Path("/makers")
DOCUMENTS_OUTPUT = Path("/var/www/maker-guide-docs/current")
LEARNER_ROUTES_PATH = Path("/etc/caddy/learner-routes.caddy")
LEARNER_HOME_ROOT = Path("/home")
VAR_LIB_ROOT = Path("/var/lib")
LEARNER_UID_MINIMUM = 20_000
LEARNER_UID_MAXIMUM = 20_999
PROTECTED_USERS = frozenset({"guide", "new", "pmuller"})


class ResetError(RuntimeError):
    """Raised when a reset request cannot safely proceed."""


def parse_arguments(arguments: list[str] | None = None) -> argparse.Namespace:
    """Parse the reset scope and its destructive confirmation."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="scope", required=True)
    learner_parser = subparsers.add_parser(
        "learner", help="Delete one learner except IRC data."
    )
    _ = learner_parser.add_argument("username")
    _ = learner_parser.add_argument("--confirm", required=True)
    _ = learner_parser.add_argument("--apply", action="store_true")
    all_parser = subparsers.add_parser("all", help="Reset all classroom runtime data.")
    _ = all_parser.add_argument("--confirm", required=True)
    _ = all_parser.add_argument("--apply", action="store_true")
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    """Run the requested reset after validating its confirmation."""
    parsed_arguments = parse_arguments(arguments)
    try:
        _require_root()
        if parsed_arguments.scope == "learner":
            _reset_learner(
                parsed_arguments.username,
                parsed_arguments.confirm,
                parsed_arguments.apply,
            )
        else:
            _reset_all(parsed_arguments.confirm, parsed_arguments.apply)
    except (OSError, ResetError, sqlite3.Error, subprocess.CalledProcessError) as error:
        print(f"kam-classroom-reset: {error}", file=sys.stderr)
        return 1
    return 0


def _require_root() -> None:
    if os.geteuid() != 0:
        raise ResetError("must run as root")


def _reset_learner(username: str, confirmation: str, apply: bool) -> None:
    _validate_learner(username)
    if confirmation != username:
        raise ResetError("--confirm must exactly match the learner username")
    if not apply:
        _print_plan(_learner_commands(username))
        return
    _run_commands(_learner_stop_commands())
    try:
        _run_commands(_learner_mutation_commands(username))
        _delete_learner_database_data(username)
        _scrub_audit_exports(username)
        _remove_path(LEARNER_HOME_ROOT / username)
        _run_commands(_learner_reconciliation_commands())
    finally:
        _run_commands(_learner_start_commands())


def _reset_all(confirmation: str, apply: bool) -> None:
    if confirmation != CONFIRM_ALL:
        raise ResetError(f"--confirm must exactly match {CONFIRM_ALL}")
    usernames = _learner_usernames()
    if not apply:
        _print_plan(_all_reset_commands(usernames))
        return
    _run_commands(_all_reset_commands(usernames))
    for username in usernames:
        _remove_path(LEARNER_HOME_ROOT / username)
    for path in _all_reset_paths():
        _remove_path(path)
    _run_commands((("/usr/sbin/sss_cache", "-E"),))
    print(
        "Reset complete. From the Salt controller, run: "
        "uv run salt-runner ssh-apply <classroom-host> roles.kam-classroom"
    )


def _validate_learner(username: str) -> None:
    if (
        username in PROTECTED_USERS
        or not username.isascii()
        or not username.replace("-", "").isalnum()
    ):
        raise ResetError(f"unsafe learner username: {username}")
    try:
        account = pwd.getpwnam(username)
    except KeyError as error:
        raise ResetError(f"unknown learner: {username}") from error
    if not LEARNER_UID_MINIMUM <= account.pw_uid <= LEARNER_UID_MAXIMUM:
        raise ResetError(f"not a classroom learner: {username}")
    if Path(account.pw_dir) != LEARNER_HOME_ROOT / username:
        raise ResetError(f"unsafe learner home: {account.pw_dir}")
    if username not in grp.getgrnam("lf2607").gr_mem:
        raise ResetError(f"not in the classroom group: {username}")


def _learner_usernames() -> tuple[str, ...]:
    usernames: list[str] = []
    for username in grp.getgrnam("lf2607").gr_mem:
        try:
            account = pwd.getpwnam(username)
        except KeyError:
            continue
        if (
            account.pw_name not in PROTECTED_USERS
            and LEARNER_UID_MINIMUM <= account.pw_uid <= LEARNER_UID_MAXIMUM
            and Path(account.pw_dir) == LEARNER_HOME_ROOT / account.pw_name
        ):
            usernames.append(account.pw_name)
    return tuple(usernames)


def _learner_commands(username: str) -> tuple[tuple[str, ...], ...]:
    return (
        _learner_stop_commands()
        + _learner_mutation_commands(username)
        + _post_reset_commands()
    )


def _learner_stop_commands() -> tuple[tuple[str, ...], ...]:
    return (
        ("/usr/bin/systemctl", "stop", "maker-guide-sync-derived-data.timer"),
        ("/usr/bin/systemctl", "stop", "maker-guide-bot.service"),
    )


def _learner_mutation_commands(username: str) -> tuple[tuple[str, ...], ...]:
    return (
        ("/usr/bin/loginctl", "terminate-user", username),
        (
            "/usr/sbin/runuser",
            "-u",
            "git",
            "--",
            "/usr/local/bin/forgejo",
            "--config",
            "/etc/forgejo/app.ini",
            "--work-path",
            "/data/forgejo",
            "admin",
            "user",
            "delete",
            "--username",
            username,
            "--purge",
        ),
        ("/usr/local/sbin/lldap-delete-user", username),
    )


def _learner_reconciliation_commands() -> tuple[tuple[str, ...], ...]:
    return (
        (
            "/usr/sbin/runuser",
            "-u",
            "maker-guide",
            "--",
            "/usr/local/bin/maker-guide-sync-derived-data",
            "--config",
            "/etc/maker-guide/config.toml",
        ),
        ("/usr/local/sbin/refresh-learner-routes",),
    )


def _learner_start_commands() -> tuple[tuple[str, ...], ...]:
    return (
        ("/usr/bin/systemctl", "start", "maker-guide-bot.service"),
        ("/usr/bin/systemctl", "start", "maker-guide-sync-derived-data.timer"),
    )


def _post_reset_commands() -> tuple[tuple[str, ...], ...]:
    return _learner_reconciliation_commands() + _learner_start_commands()


def _all_reset_commands(usernames: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    return tuple(
        ("/usr/bin/loginctl", "terminate-user", username) for username in usernames
    ) + tuple(
        ("/usr/bin/systemctl", "stop", service_name)
        for service_name in (
            "maker-guide-sync-derived-data.timer",
            "maker-guide-bot.service",
            "forgejo.service",
            "ergo.service",
            "authelia.service",
            "lldap.service",
        )
    )


def _all_reset_paths() -> tuple[Path, ...]:
    return (
        DATABASE_PATH,
        DATABASE_PATH.with_name(f"{DATABASE_PATH.name}-shm"),
        DATABASE_PATH.with_name(f"{DATABASE_PATH.name}-wal"),
        AUDIT_ROOT,
        Path("/var/lib/maker-guide/shiv"),
        Path("/var/lib/maker-guide/.shiv"),
        Path("/root/.shiv"),
        *sorted(VAR_LIB_ROOT.glob("kam-*")),
        MAKERS_ROOT,
        DOCUMENTS_OUTPUT,
        LEARNER_ROUTES_PATH,
        Path("/data/lldap"),
        Path("/data/forgejo"),
        Path("/data/ergo"),
        Path("/data/authelia"),
    )


def _run_commands(commands: Iterable[tuple[str, ...]]) -> None:
    for command in commands:
        if command[:2] == ("/usr/bin/loginctl", "terminate-user"):
            completed_process = subprocess.run(command, capture_output=True, text=True)
            if (
                completed_process.returncode
                and "not logged in or lingering" not in completed_process.stderr
            ):
                raise subprocess.CalledProcessError(
                    completed_process.returncode,
                    command,
                    completed_process.stdout,
                    completed_process.stderr,
                )
        else:
            _ = subprocess.run(command, check=True)


def _print_plan(commands: Iterable[tuple[str, ...]]) -> None:
    for command in commands:
        print(" ".join(command))


def _delete_learner_database_data(username: str) -> None:
    with sqlite3.connect(DATABASE_PATH) as database_connection:
        _ = database_connection.execute("pragma foreign_keys = on")
        _ = database_connection.execute(
            "delete from audit_events where handle = ?", (username,)
        )
        _ = database_connection.execute(
            "delete from outbox_items where payload_json like ?", (f"%{username}%",)
        )
        _ = database_connection.execute(
            "delete from learners where handle = ?", (username,)
        )


def _scrub_audit_exports(username: str) -> None:
    if not AUDIT_ROOT.is_dir():
        return
    for audit_path in AUDIT_ROOT.glob("*.jsonl"):
        _atomic_write_lines(
            audit_path,
            tuple(
                line
                for line in audit_path.read_text(encoding="utf-8").splitlines()
                if username not in line
            ),
        )


def _atomic_write_lines(path: Path, lines: tuple[str, ...]) -> None:
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)
        if lines:
            _ = temporary_file.write("\n".join(lines) + "\n")
        temporary_file.flush()
        os.fsync(temporary_file.fileno())
    _ = temporary_path.replace(path)


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path)


if __name__ == "__main__":
    raise SystemExit(main())
