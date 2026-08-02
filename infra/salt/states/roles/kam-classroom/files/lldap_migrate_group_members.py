#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lldap_ensure_user import (  # pyright: ignore[reportImplicitRelativeImport]
    LldapError,
    login,
    migrate_group_members,
    read_environment_file,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add legacy LLDAP group members to replacement groups."
    )
    _ = parser.add_argument("legacy_group")
    _ = parser.add_argument("target_groups", nargs="+")
    _ = parser.add_argument("--base-url", default="http://127.0.0.1:17170/")
    _ = parser.add_argument("--admin-username", default="admin")
    _ = parser.add_argument("--environment-file", default="/etc/lldap/lldap.env")
    _ = parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    environment_file = read_environment_file(Path(arguments.environment_file))
    admin_password = environment_file.get("LLDAP_LDAP_USER_PASS")
    if not admin_password:
        raise LldapError(
            f"{arguments.environment_file} does not define LLDAP_LDAP_USER_PASS"
        )
    token = login(arguments.base_url, arguments.admin_username, admin_password)
    changed = migrate_group_members(
        arguments.base_url,
        token,
        arguments.legacy_group,
        arguments.target_groups,
        arguments.check,
    )
    if arguments.check and changed:
        raise LldapError("Legacy group members need migration")
    print(arguments.legacy_group)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LldapError as error:
        print(f"lldap-migrate-group-members: {error}", file=sys.stderr)
        raise SystemExit(1)
