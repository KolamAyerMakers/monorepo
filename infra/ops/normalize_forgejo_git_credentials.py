#!/usr/bin/env python3
"""One-time Forgejo HTTPS credential backfill for existing classroom accounts."""

from __future__ import annotations

import argparse
import grp
import os
import pwd
import subprocess
import uuid
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit


FORGEJO_BINARY = "/usr/local/bin/forgejo"
FORGEJO_CONFIG = "/etc/forgejo/app.ini"
FORGEJO_WORK_PATH = "/data/forgejo"
FORGEJO_RUN_USER = "git"
TOKEN_SCOPES = "read:repository,write:repository"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--forgejo-url", required=True)
    _ = parser.add_argument("--apply", action="store_true")
    _ = parser.add_argument("--all", action="store_true", help="Configure linux-foundations members.")
    _ = parser.add_argument("username", nargs="*")
    arguments = parser.parse_args()
    if arguments.all == bool(arguments.username):
        parser.error("provide usernames or use --all")
    return arguments


def usernames(arguments: argparse.Namespace) -> tuple[str, ...]:
    if arguments.all:
        return tuple(member for member in grp.getgrnam("linux-foundations").gr_mem if member)
    return tuple(arguments.username)


def credential_url(forgejo_url: str, username: str, token: str) -> str:
    parsed_url = urlsplit(forgejo_url.removesuffix("/"))
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ValueError("--forgejo-url must be an HTTPS URL")
    return urlunsplit(
        (
            parsed_url.scheme,
            f"{quote(username, safe='')}:{quote(token, safe='')}@{parsed_url.netloc}",
            "",
            "",
            "",
        )
    )


def generate_token(username: str) -> str | None:
    completed_process = subprocess.run(
        [
            "/usr/sbin/runuser",
            "-u",
            FORGEJO_RUN_USER,
            "--",
            FORGEJO_BINARY,
            "--config",
            FORGEJO_CONFIG,
            "--work-path",
            FORGEJO_WORK_PATH,
            "admin",
            "user",
            "generate-access-token",
            "--username",
            username,
            "--token-name",
            f"classroom-git-{uuid.uuid4().hex}",
            "--raw",
            "--scopes",
            TOKEN_SCOPES,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed_process.returncode != 0:
        if "user does not exist" in completed_process.stderr.lower():
            return None
        raise RuntimeError(completed_process.stderr.strip() or f"Forgejo failed for {username}")
    if not (token := completed_process.stdout.strip()):
        raise RuntimeError(f"Forgejo returned no token for {username}")
    return token


def configure_git_credentials(forgejo_url: str, username: str) -> bool:
    user_record = pwd.getpwnam(username)
    credentials_directory = Path(user_record.pw_dir) / ".config" / "git"
    credentials_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    credentials_file = credentials_directory / "credentials"
    if (token := generate_token(username)) is None:
        return False
    _ = credentials_file.write_text(
        credential_url(forgejo_url, username, token) + "\n",
        encoding="utf-8",
    )
    os.chown(credentials_directory, user_record.pw_uid, user_record.pw_gid)
    os.chown(credentials_file, user_record.pw_uid, user_record.pw_gid)
    os.chmod(credentials_directory, 0o700)
    os.chmod(credentials_file, 0o600)
    configuration_file = Path(user_record.pw_dir) / ".gitconfig"
    _ = subprocess.run(
        [
            "/usr/bin/git",
            "config",
            "--file",
            str(configuration_file),
            "credential.helper",
            f"store --file {credentials_file}",
        ],
        check=True,
    )
    os.chown(configuration_file, user_record.pw_uid, user_record.pw_gid)
    os.chmod(configuration_file, 0o600)
    return True


def main() -> int:
    arguments = parse_arguments()
    if arguments.apply and os.geteuid() != 0:
        raise SystemExit("run as root")
    for username in usernames(arguments):
        if not arguments.apply:
            print(f"would configure Git credentials for {username}")
            continue
        if configure_git_credentials(arguments.forgejo_url, username):
            print(f"configured Git credentials for {username}")
        else:
            print(f"skipped {username}: no Forgejo account")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
