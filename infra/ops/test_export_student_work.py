#!/usr/bin/env python3
"""Offline checks only: never contact the classroom or require root."""

from __future__ import annotations

import subprocess
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import patch

import export_student_work


def test_private_export_preserves_work_without_following_links() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        home = root / "home"
        (home / "src/.git").mkdir(parents=True)
        (home / "src/.git/config").write_text("keep Git history", encoding="utf-8")
        (home / "playground").mkdir()
        for directory in ("src/node_modules", "src/site/node_modules", "playground/node_modules"):
            (home / directory).mkdir(parents=True)
            (home / directory / "dependency.js").write_text("omit dependency", encoding="utf-8")
        (home / "src/site/package.json").write_text("{}", encoding="utf-8")
        (home / "src/site/package-lock.json").write_text("{}", encoding="utf-8")
        private = root / "outside-secret"
        private.write_text("not student work", encoding="utf-8")
        (home / "src/link").symlink_to(private)
        destination = root / "student.tar.gz"

        def local_tar(_host: str, *command: str) -> list[str]:
            arguments = list(command)
            arguments[arguments.index("-C") + 1] = str(home)
            return arguments

        with patch.object(export_student_work, "_ssh", side_effect=local_tar) as remote_command:
            export_student_work._export_archive(
                "not-a-real-host",
                "student",
                ["src", "playground"],
                destination,
            )
        remote_command.assert_called_once_with(
            "not-a-real-host",
            "tar",
            "-czf",
            "-",
            "-C",
            "/home/student",
            "--exclude=node_modules",
            "--files-from=/dev/null",
            "--",
            "src",
            "playground",
        )
        assert destination.stat().st_mode & 0o777 == 0o600
        with tarfile.open(destination) as archive:
            assert archive.getmember("src/.git/config").isfile()
            assert archive.getmember("src/link").issym()
            assert archive.getmember("src/site/package.json").isfile()
            assert archive.getmember("src/site/package-lock.json").isfile()
            assert all("node_modules" not in Path(name).parts for name in archive.getnames())
            assert {Path(name).parts[0] for name in archive.getnames()} == {"src", "playground"}
        failed = root / "failed.tar.gz"
        with patch.object(export_student_work, "_ssh", return_value=["false"]):
            try:
                export_student_work._export_archive("not-a-real-host", "student", [], failed)
            except subprocess.CalledProcessError:
                pass
            else:
                raise AssertionError("A failed transfer must fail the export")
        assert not failed.exists()
        assert failed.with_name("failed.tar.gz.partial").exists()
        for inventory in ('{"../escape": ["src"]}', '{"student": [".ssh"]}', "{}"):
            with patch.object(
                export_student_work.subprocess, "check_output", return_value=inventory
            ):
                try:
                    export_student_work._students("not-a-real-host")
                except ValueError:
                    pass
                else:
                    raise AssertionError("Invalid inventory must be refused")


if __name__ == "__main__":
    test_private_export_preserves_work_without_following_links()
    print("student work export checks passed")
