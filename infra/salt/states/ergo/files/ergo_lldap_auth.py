#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass


USERNAME_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")


@dataclass(frozen=True, slots=True)
class Settings:
    ldap_uri: str
    base_dn: str
    allowed_groups: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AuthRequest:
    account_name: str
    passphrase: str


def parse_arguments() -> Settings:
    parser = argparse.ArgumentParser(description="Authenticate Ergo users with LLDAP.")
    _ = parser.add_argument("--ldap-uri", required=True)
    _ = parser.add_argument("--base-dn", required=True)
    _ = parser.add_argument(
        "--allowed-group",
        action="append",
        default=[],
        dest="allowed_groups",
    )
    _ = parser.add_argument(
        "--required-group",
        action="append",
        default=[],
        dest="required_groups",
        help=argparse.SUPPRESS,
    )
    arguments = parser.parse_args()
    allowed_groups = tuple(
        group_name
        for group_name in [*arguments.allowed_groups, *arguments.required_groups]
        if group_name
    )
    if not allowed_groups:
        raise ValueError("at least one allowed group is required")
    return Settings(
        ldap_uri=str(arguments.ldap_uri),
        base_dn=str(arguments.base_dn),
        allowed_groups=allowed_groups,
    )


def parse_request() -> AuthRequest:
    payload = json.loads(sys.stdin.readline())
    account_name = str(payload.get("accountName", ""))
    passphrase = str(payload.get("passphrase", ""))
    if not USERNAME_PATTERN.fullmatch(account_name):
        raise ValueError("invalid account name")
    if not passphrase:
        raise ValueError("empty passphrase")
    return AuthRequest(account_name=account_name, passphrase=passphrase)


def user_distinguished_name(settings: Settings, account_name: str) -> str:
    return f"uid={account_name},ou=people,{settings.base_dn}"


def group_distinguished_name(settings: Settings, group_name: str) -> str:
    return f"cn={group_name},ou=groups,{settings.base_dn}"


def ldap_filter(settings: Settings, request: AuthRequest) -> str:
    return f"(uniqueMember={user_distinguished_name(settings, request.account_name)})"


def is_group_member(
    settings: Settings,
    request: AuthRequest,
    group_name: str,
) -> bool:
    group_name = group_distinguished_name(settings, group_name)
    completed_process = subprocess.run(
        [
            "/usr/bin/ldapsearch",
            "-LLL",
            "-x",
            "-H",
            settings.ldap_uri,
            "-D",
            user_distinguished_name(settings, request.account_name),
            "-w",
            request.passphrase,
            "-b",
            group_name,
            ldap_filter(settings, request),
            "dn",
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        timeout=5,
    )
    return (
        completed_process.returncode == 0
        and f"dn: {group_name}" in completed_process.stdout
    )


def authenticate(settings: Settings, request: AuthRequest) -> bool:
    return any(
        is_group_member(settings, request, group_name)
        for group_name in settings.allowed_groups
    )


def write_response(success: bool, account_name: str = "", error: str = "") -> None:
    response = {
        "success": success,
        "accountName": account_name if success else "",
        "error": error,
    }
    print(json.dumps(response, separators=(",", ":")), flush=True)


def main() -> int:
    try:
        settings = parse_arguments()
        request = parse_request()
    except (json.JSONDecodeError, ValueError) as error:
        write_response(False, error=str(error))
        return 0

    try:
        write_response(
            authenticate(settings, request),
            account_name=request.account_name,
        )
    except (OSError, subprocess.SubprocessError) as error:
        write_response(False, error=str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
