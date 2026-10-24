#!/usr/bin/env python3
"""Download one private tarball per lf2607 student into a NEW local directory.

Usage: python3 infra/ops/export_student_work.py /private/path/to/new-export
Includes hidden files and Git history, but no node_modules; review secrets before sharing.
Symlinks are archived as links, never followed. No remote staging files are created.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
from pathlib import Path
from textwrap import dedent
from typing import cast


SOURCE_DIRECTORIES = ("src", "playground", "scripts")
_INVENTORY = dedent("""\
    import json
    import pwd
    import sqlite3
    from pathlib import Path

    students = {}
    with sqlite3.connect('file:/var/lib/maker-guide/state.db?mode=ro', uri=True) as connection:
        handles = connection.execute(
            'select handle from cohort_memberships '
            'where course_id = ? and rank_eligible = 1 order by handle', ('lf2607',)
        ).fetchall()
    for (handle,) in handles:
        account = pwd.getpwnam(handle)
        home = Path(account.pw_dir)
        if not 20000 <= account.pw_uid <= 20999 or home != Path('/home') / handle:
            raise RuntimeError(f'Not a student home: {handle}')
        if home.is_symlink() or not home.is_dir() or home.stat().st_uid != account.pw_uid:
            raise RuntimeError(f'Unsafe home: {home}')
        directories = []
        for name in ('src', 'playground', 'scripts'):
            directory = home / name
            if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
                raise RuntimeError(f'Not a real directory: {directory}')
            if directory.is_dir():
                directories.append(name)
        students[handle] = directories
    print(json.dumps(students))
    """)


def _ssh(host: str, *command: str) -> list[str]:
    return [
        "ssh",
        "-T",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        host,
        shlex.join(command),
    ]


def _students(host: str) -> dict[str, list[str]]:
    inventory: object = json.loads(
        subprocess.check_output(
            _ssh(host, "python3", "-"),
            input=_INVENTORY,
            text=True,
        )
    )
    if not isinstance(inventory, dict) or not inventory:
        raise ValueError("No student inventory received")
    for handle, directories in inventory.items():
        if not isinstance(handle, str) or not re.fullmatch(r"[a-z][a-z0-9-]{1,31}", handle):
            raise ValueError(f"Invalid student handle: {handle!r}")
        if not isinstance(directories, list) or any(
            name not in SOURCE_DIRECTORIES for name in directories
        ):
            raise ValueError(f"Invalid source directories for {handle}")
    return cast("dict[str, list[str]]", inventory)


def _export_archive(host: str, handle: str, directories: list[str], destination: Path) -> None:
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    partial = destination.with_name(destination.name + ".partial")
    with partial.open("xb") as output:
        os.fchmod(output.fileno(), 0o600)
        # Root can read files locked during permission exercises; never dereference links.
        subprocess.run(
            _ssh(
                host,
                "tar",
                "-czf",
                "-",
                "-C",
                f"/home/{handle}",
                "--exclude=node_modules",
                "--files-from=/dev/null",
                "--",
                *directories,
            ),
            stdout=output,
            check=True,
        )
    # An interrupted transfer or invalid archive never gets a final .tar.gz name.
    subprocess.run(["tar", "-tzf", str(partial)], stdout=subprocess.DEVNULL, check=True)
    partial.rename(destination)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="New private local export directory")
    parser.add_argument("--host", default="root@lf2607.kolamayermakers.org")
    arguments = parser.parse_args()
    students = _students(arguments.host)
    destination = arguments.output.expanduser().resolve()
    destination.mkdir(mode=0o700, parents=True)
    for handle, directories in students.items():
        missing = sorted(set(SOURCE_DIRECTORIES) - set(directories))
        print(f"{handle}: missing {', '.join(missing) if missing else 'nothing'}", flush=True)
        _export_archive(arguments.host, handle, directories, destination / f"{handle}.tar.gz")
    manifest = destination / "manifest.json"
    manifest.write_text(json.dumps(students, indent=2) + "\n", encoding="utf-8")
    manifest.chmod(0o600)
    print(f"Exported {len(students)} verified archives to {destination}")


if __name__ == "__main__":
    main()
