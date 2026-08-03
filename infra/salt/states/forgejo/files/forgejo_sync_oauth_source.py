#!/usr/bin/env python3
from __future__ import annotations

import argparse
import configparser
import hmac
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import cast


class ForgejoError(Exception):
    pass


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synchronize a Forgejo OAuth source.")
    _ = parser.add_argument("--name", required=True)
    _ = parser.add_argument("--provider", required=True)
    _ = parser.add_argument("--client-id", required=True)
    _ = parser.add_argument("--client-secret-file", required=True)
    _ = parser.add_argument("--auto-discover-url", required=True)
    _ = parser.add_argument("--scope", action="append", default=[])
    _ = parser.add_argument("--group-claim-name")
    _ = parser.add_argument("--skip-local-2fa", action="store_true")
    _ = parser.add_argument("--check", action="store_true")
    _ = parser.add_argument("--forgejo-binary", default="/usr/local/bin/forgejo")
    _ = parser.add_argument("--configuration-file", default="/etc/forgejo/app.ini")
    _ = parser.add_argument("--work-path", default="/data/forgejo")
    return parser.parse_args()


def run_command(command: list[str]) -> str:
    completed_process = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed_process.returncode != 0:
        message = completed_process.stderr.strip() or completed_process.stdout.strip()
        raise ForgejoError(message)
    return completed_process.stdout


def forgejo_command(arguments: argparse.Namespace, *command: str) -> list[str]:
    return [
        arguments.forgejo_binary,
        "--config",
        arguments.configuration_file,
        "--work-path",
        arguments.work_path,
        *command,
    ]


def find_auth_source_id(arguments: argparse.Namespace) -> str | None:
    output = run_command(forgejo_command(arguments, "admin", "auth", "list"))
    for line in output.splitlines():
        columns = line.split()
        if len(columns) >= 2 and columns[1] == arguments.name:
            return columns[0]
    return None


def oauth_source_matches(arguments: argparse.Namespace) -> bool:
    configuration = configparser.ConfigParser()
    _ = configuration.read(arguments.configuration_file)
    try:
        database_path = configuration["database"]["PATH"]
    except KeyError as error:
        raise ForgejoError("Forgejo database path is not configured") from error

    with sqlite3.connect(f"file:{database_path}?mode=ro", uri=True) as connection:
        row = connection.execute(
            "SELECT type, cfg FROM login_source WHERE name = ?", (arguments.name,)
        ).fetchone()
    if row is None or row[0] != 6:
        return False
    try:
        source_configuration = cast(object, json.loads(row[1]))
    except (TypeError, json.JSONDecodeError) as error:
        raise ForgejoError("OAuth source configuration is invalid") from error
    if not isinstance(source_configuration, dict):
        raise ForgejoError("OAuth source configuration is invalid")
    oauth_configuration = cast(dict[str, object], source_configuration)
    stored_secret = oauth_configuration.get("ClientSecret")
    if not isinstance(stored_secret, str):
        return False

    return (
        oauth_configuration.get("Provider") == arguments.provider
        and oauth_configuration.get("ClientID") == arguments.client_id
        and hmac.compare_digest(
            stored_secret,
            Path(arguments.client_secret_file).read_text(encoding="utf-8").strip(),
        )
        and oauth_configuration.get("OpenIDConnectAutoDiscoveryURL")
        == arguments.auto_discover_url
        and oauth_configuration.get("Scopes") == arguments.scope
        and oauth_configuration.get("GroupClaimName", "")
        == (arguments.group_claim_name or "")
    )


def oauth_arguments(arguments: argparse.Namespace) -> list[str]:
    client_secret = (
        Path(arguments.client_secret_file).read_text(encoding="utf-8").strip()
    )
    command_arguments = [
        "--name",
        arguments.name,
        "--provider",
        arguments.provider,
        "--key",
        arguments.client_id,
        "--secret",
        client_secret,
        "--auto-discover-url",
        arguments.auto_discover_url,
    ]
    for scope in arguments.scope:
        command_arguments.extend(["--scopes", scope])
    if arguments.group_claim_name:
        command_arguments.extend(["--group-claim-name", arguments.group_claim_name])
    if arguments.skip_local_2fa:
        command_arguments.append("--skip-local-2fa")
    return command_arguments


def synchronize_oauth_source(arguments: argparse.Namespace) -> None:
    if arguments.check:
        if not oauth_source_matches(arguments):
            raise ForgejoError(f"OAuth source differs: {arguments.name}")
        return

    auth_source_id = find_auth_source_id(arguments)
    if auth_source_id is None:
        command = forgejo_command(
            arguments,
            "admin",
            "auth",
            "add-oauth",
            *oauth_arguments(arguments),
        )
    else:
        command = forgejo_command(
            arguments,
            "admin",
            "auth",
            "update-oauth",
            "--id",
            auth_source_id,
            *oauth_arguments(arguments),
        )
    _ = run_command(command)


def main() -> int:
    try:
        synchronize_oauth_source(parse_arguments())
    except ForgejoError as error:
        print(f"forgejo-sync-oauth-source: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
