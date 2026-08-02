#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import cast


GENERATED_PASSWORD_ATTEMPTS = 10


class LldapError(Exception):
    pass


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reset an LLDAP user's password.")
    _ = parser.add_argument("username")
    _ = parser.add_argument("--password-stdin", action="store_true")
    _ = parser.add_argument("--check", action="store_true")
    _ = parser.add_argument("--base-url", default="http://127.0.0.1:17170/")
    _ = parser.add_argument("--admin-username", default="admin")
    _ = parser.add_argument("--environment-file", default="/etc/lldap/lldap.env")
    _ = parser.add_argument("--pwscore-command", default="/usr/bin/pwscore")
    return parser.parse_args()


def read_environment_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#"):
            continue
        if "=" not in stripped_line:
            continue
        key, value = stripped_line.split("=", 1)
        values[key] = value
    return values


def append_path(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def post_json(
    url: str,
    payload: dict[str, object],
    token: str | None = None,
) -> dict[str, object]:
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return cast(dict[str, object], json.loads(response.read().decode("utf-8")))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise LldapError(f"HTTP {error.code} from {url}: {body}") from error
    except urllib.error.URLError as error:
        raise LldapError(f"Could not connect to {url}: {error}") from error


def login(base_url: str, username: str, password: str) -> str:
    response = post_json(
        append_path(base_url, "/auth/simple/login"),
        {"username": username, "password": password},
    )
    try:
        return str(response["token"])
    except KeyError as error:
        raise LldapError("Login response did not contain a token") from error


def set_password(
    base_url: str,
    token: str,
    username: str,
    password: str,
) -> None:
    environment = os.environ.copy()
    environment["LLDAP_USER_PASSWORD"] = password
    _ = subprocess.run(
        [
            "/usr/local/bin/lldap_set_password",
            "--base-url",
            base_url,
            "--token",
            token,
            "--username",
            username,
        ],
        env=environment,
        check=True,
    )


def generate_password() -> str:
    result = subprocess.run(
        [
            "/usr/bin/diceware",
            "--no-caps",
            "--delimiter",
            "-",
            "--num",
            "6",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    password = result.stdout.strip()
    if not password:
        raise LldapError("diceware did not generate a password")
    return password


def password_strength_error(
    pwscore_command: str,
    username: str,
    password: str,
) -> str | None:
    if not password:
        return "The password is empty."
    if username in password.lower():
        return "It contains the username."
    try:
        completed_process = subprocess.run(
            [pwscore_command],
            check=False,
            input=password + "\n",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        return f"{pwscore_command} was not found."
    if completed_process.returncode == 0:
        return None
    return (
        completed_process.stderr.strip()
        or completed_process.stdout.strip()
        or "The password did not pass the system strength policy."
    )


def validate_password(pwscore_command: str, username: str, password: str) -> None:
    error = password_strength_error(pwscore_command, username, password)
    if error is not None:
        raise LldapError(f"Password rejected: {error}")


def generate_compliant_password(pwscore_command: str, username: str) -> str:
    last_error = "unknown password quality failure"
    remaining_attempts = GENERATED_PASSWORD_ATTEMPTS
    while remaining_attempts > 0:
        remaining_attempts -= 1
        password = generate_password()
        error = password_strength_error(pwscore_command, username, password)
        if error is None:
            return password
        last_error = error
    raise LldapError(
        "diceware did not generate a compliant password after "
        f"{GENERATED_PASSWORD_ATTEMPTS} attempts: {last_error}"
    )


def resolve_password(
    pwscore_command: str,
    username: str,
    password_stdin: bool,
) -> str:
    if not password_stdin:
        return generate_compliant_password(pwscore_command, username)
    password = sys.stdin.read().rstrip("\n")
    validate_password(pwscore_command, username, password)
    return password


def read_check_password(password_stdin: bool) -> str:
    if not password_stdin:
        raise LldapError("--check requires --password-stdin")
    password = sys.stdin.read().rstrip("\n")
    if not password:
        raise LldapError("The password is empty.")
    return password


def main() -> int:
    arguments = parse_arguments()
    if arguments.check:
        _ = login(
            arguments.base_url,
            arguments.username,
            read_check_password(arguments.password_stdin),
        )
        return 0

    environment_file = read_environment_file(Path(arguments.environment_file))
    admin_password = environment_file.get("LLDAP_LDAP_USER_PASS")
    if not admin_password:
        raise LldapError(
            f"{arguments.environment_file} does not define LLDAP_LDAP_USER_PASS"
        )

    password = resolve_password(
        arguments.pwscore_command,
        arguments.username,
        arguments.password_stdin,
    )
    set_password(
        arguments.base_url,
        login(arguments.base_url, arguments.admin_username, admin_password),
        arguments.username,
        password,
    )
    print(arguments.username)
    if not arguments.password_stdin:
        print(password)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LldapError as error:
        print(f"lldap-set-password: {error}", file=sys.stderr)
        raise SystemExit(1)
