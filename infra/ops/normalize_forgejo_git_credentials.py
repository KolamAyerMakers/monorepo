#!/usr/bin/env python3
"""Provision Forgejo Git credentials or repair learner home directory roots."""

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
TOKEN_SCOPES = "write:user,read:repository,write:repository"
HOME_ROOT = Path("/home")
HOME_DIRECTORY_MODE = 0o711


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    operation_group = parser.add_mutually_exclusive_group(required=True)
    _ = operation_group.add_argument("--forgejo-url")
    _ = operation_group.add_argument(
        "--repair-home-ownership",
        action="store_true",
        help="Repair only existing /home/<username> directory roots.",
    )
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


def prepare_home_directory(
    user_record: pwd.struct_passwd,
    *,
    create: bool,
) -> Path | None:
    home_path = Path(user_record.pw_dir)
    expected_home_path = HOME_ROOT / user_record.pw_name
    if home_path != expected_home_path:
        raise ValueError(f"refusing unexpected home path for {user_record.pw_name}: {home_path}")
    if home_path.is_symlink():
        raise ValueError(f"refusing symlink home path: {home_path}")
    home_was_created = False
    if not home_path.exists():
        if not create:
            return None
        home_path.mkdir(mode=HOME_DIRECTORY_MODE)
        home_was_created = True
    if home_path.is_symlink() or not home_path.is_dir():
        raise ValueError(f"refusing non-directory home path: {home_path}")
    home_status = home_path.stat()
    if home_status.st_uid not in (0, user_record.pw_uid):
        raise ValueError(f"refusing home owned by unexpected user: {home_path}")
    if (
        home_was_created
        or home_status.st_uid != user_record.pw_uid
        or home_status.st_gid != user_record.pw_gid
    ):
        os.chown(home_path, user_record.pw_uid, user_record.pw_gid)
    if home_was_created or home_status.st_uid == 0:
        os.chmod(home_path, HOME_DIRECTORY_MODE)
    return home_path


def configure_git_credentials(forgejo_url: str, username: str) -> bool:
    user_record = pwd.getpwnam(username)
    home_path = prepare_home_directory(user_record, create=True)
    if home_path is None:
        raise RuntimeError(f"could not create home directory for {username}")
    if (token := generate_token(username)) is None:
        return False
    credentials_directory = home_path / ".config" / "git"
    configuration_directory = credentials_directory.parent
    data_directory = home_path / ".local" / "share"
    credentials_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    data_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    credentials_file = credentials_directory / "credentials"
    _ = credentials_file.write_text(
        credential_url(forgejo_url, username, token) + "\n",
        encoding="utf-8",
    )
    os.chown(configuration_directory, user_record.pw_uid, user_record.pw_gid)
    os.chown(credentials_directory, user_record.pw_uid, user_record.pw_gid)
    os.chown(credentials_file, user_record.pw_uid, user_record.pw_gid)
    os.chown(data_directory.parent, user_record.pw_uid, user_record.pw_gid)
    os.chown(data_directory, user_record.pw_uid, user_record.pw_gid)
    os.chmod(configuration_directory, 0o700)
    os.chmod(credentials_directory, 0o700)
    os.chmod(credentials_file, 0o600)
    os.chmod(data_directory.parent, 0o700)
    os.chmod(data_directory, 0o700)
    configuration_file = home_path / ".gitconfig"
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
    _ = subprocess.run(
        [
            "/usr/sbin/runuser",
            "-u",
            username,
            "--",
            "/usr/bin/env",
            f"HOME={user_record.pw_dir}",
            "/usr/local/bin/fj",
            "--host",
            forgejo_url.removesuffix("/") + "/",
            "auth",
            "add-token",
        ],
        input=token + "\n",
        check=True,
        text=True,
    )
    return True


def repair_home_ownership(username: str) -> bool:
    user_record = pwd.getpwnam(username)
    return prepare_home_directory(user_record, create=False) is not None


def main() -> int:
    arguments = parse_arguments()
    if arguments.apply and os.geteuid() != 0:
        raise SystemExit("run as root")
    for username in usernames(arguments):
        if arguments.repair_home_ownership:
            if not arguments.apply:
                print(f"would repair home ownership for {username}")
            elif repair_home_ownership(username):
                print(f"repaired home ownership for {username}")
            else:
                print(f"skipped {username}: home directory does not exist")
            continue
        if not arguments.apply:
            print(f"would configure Git credentials for {username}")
            continue
        forgejo_url = arguments.forgejo_url
        if forgejo_url is None:
            raise RuntimeError("--forgejo-url is required for credential provisioning")
        if configure_git_credentials(forgejo_url, username):
            print(f"configured Git credentials for {username}")
        else:
            print(f"skipped {username}: no Forgejo account")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
