#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import cast


class LldapError(Exception):
    pass


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Delete an LLDAP user.")
    _ = parser.add_argument("username")
    _ = parser.add_argument("--base-url", default="http://127.0.0.1:17170/")
    _ = parser.add_argument("--admin-username", default="admin")
    _ = parser.add_argument("--environment-file", default="/etc/lldap/lldap.env")
    _ = parser.add_argument("--skip-sss-cache", action="store_true")
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


def graphql(
    base_url: str,
    token: str,
    query: str,
    variables: dict[str, object],
) -> dict[str, object]:
    response = post_json(
        append_path(base_url, "/api/graphql"),
        {"query": query, "variables": variables},
        token=token,
    )
    if response.get("errors"):
        raise LldapError(json.dumps(response["errors"], indent=2))
    data = response.get("data")
    if not isinstance(data, dict):
        raise LldapError("GraphQL response did not contain a data object")
    return cast(dict[str, object], data)


def delete_user(base_url: str, token: str, username: str) -> None:
    _ = graphql(
        base_url,
        token,
        """
        mutation DeleteUser($userId: String!) {
          deleteUser(userId: $userId) { ok }
        }
        """,
        {"userId": username},
    )


def invalidate_sss_cache(username: str) -> None:
    if not Path("/usr/sbin/sss_cache").is_file():
        return
    _ = subprocess.run(["/usr/sbin/sss_cache", "-u", username], check=True)


def main() -> int:
    arguments = parse_arguments()
    environment_file = read_environment_file(Path(arguments.environment_file))
    admin_password = environment_file.get("LLDAP_LDAP_USER_PASS")
    if not admin_password:
        raise LldapError(
            f"{arguments.environment_file} does not define LLDAP_LDAP_USER_PASS"
        )

    delete_user(
        arguments.base_url,
        login(arguments.base_url, arguments.admin_username, admin_password),
        arguments.username,
    )
    if not arguments.skip_sss_cache:
        invalidate_sss_cache(arguments.username)
    print(arguments.username)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (LldapError, subprocess.CalledProcessError) as error:
        print(f"lldap-delete-user: {error}", file=sys.stderr)
        raise SystemExit(1)
