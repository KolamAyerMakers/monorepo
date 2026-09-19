#!/usr/bin/env python3
"""Reconcile lingering for explicit members of the Salt-selected course group."""

from __future__ import annotations

import argparse
import grp
import json
import os
import pwd
import re
import subprocess
import sys
from pathlib import Path

POLICY_FILE = Path("/etc/kam-classroom-lingering.json")
LINGER_DIRECTORY = Path("/var/lib/systemd/linger")


def main(arguments: list[str] | None = None) -> int:
    """Enable group members, or disable them before deleting their identities."""
    if os.geteuid() != 0:
        raise PermissionError("must run as root")
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--disable", action="store_true")
    _ = parser.add_argument("username", nargs="?")
    options = parser.parse_args(arguments)
    policy = json.loads(POLICY_FILE.read_text(encoding="utf-8"))
    group_name = policy["group"]
    uid_minimum = policy["uid_minimum"]
    uid_maximum = policy["uid_maximum"]
    if re.fullmatch(r"[a-z][a-z0-9-]*", group_name) is None:
        raise ValueError("invalid lingering policy group")
    if not 0 < uid_minimum <= uid_maximum:
        raise ValueError("invalid lingering policy UID range")
    # Populate before expiring: sss_cache fails when no cached group exists yet.
    _ = grp.getgrnam(group_name)
    _ = subprocess.run(["/usr/sbin/sss_cache", "-g", group_name], check=True)
    # ponytail: explicit members only; revoke lingering before removing membership.
    usernames = sorted(set(grp.getgrnam(group_name).gr_mem))
    if options.username is not None:
        if options.username not in usernames and not options.disable:
            raise ValueError(f"not in lingering policy group: {options.username}")
        usernames = [name for name in usernames if name == options.username]
    for username in usernames:
        if re.fullmatch(r"[a-z][a-z0-9-]*", username) is None:
            raise ValueError(f"unsafe participant name: {username}")
        account = pwd.getpwnam(username)
        if (
            account.pw_name != username
            or not uid_minimum <= account.pw_uid <= uid_maximum
            or account.pw_dir != f"/home/{username}"
            or pwd.getpwuid(account.pw_uid).pw_name != username
        ):
            raise ValueError(f"unsafe participant identity: {username}")
    changed = False
    for username in usernames:
        if (LINGER_DIRECTORY / username).exists() == (not options.disable):
            continue
        _ = subprocess.run(
            [
                "/usr/bin/loginctl",
                "disable-linger" if options.disable else "enable-linger",
                "--",
                username,
            ],
            check=True,
        )
        changed = True
    print(json.dumps({"changed": changed, "comment": "Course lingering reconciled"}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"kam-classroom-lingering: {error}", file=sys.stderr)
        raise SystemExit(1)
