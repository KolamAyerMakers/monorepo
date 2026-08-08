#!/usr/bin/env python3
"""Check Forgejo credential normalization does not damage learner homes."""

import importlib.machinery
import importlib.util
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).with_name("normalize_forgejo_git_credentials.py")
SCRIPT_LOADER = importlib.machinery.SourceFileLoader(
    "normalize_forgejo_git_credentials", str(SCRIPT_PATH)
)
SCRIPT_SPECIFICATION = importlib.util.spec_from_loader(
    SCRIPT_LOADER.name, SCRIPT_LOADER
)
assert SCRIPT_SPECIFICATION is not None
normalize_forgejo_git_credentials = importlib.util.module_from_spec(SCRIPT_SPECIFICATION)
sys.modules[SCRIPT_LOADER.name] = normalize_forgejo_git_credentials
SCRIPT_LOADER.exec_module(normalize_forgejo_git_credentials)


def test_configure_owns_absent_home_before_generating_token() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        home_root = Path(temporary_directory) / "home"
        home_root.mkdir()
        home_path = home_root / "alice"
        user_record = SimpleNamespace(
            pw_name="alice",
            pw_dir=str(home_path),
            pw_uid=os.getuid(),
            pw_gid=os.getgid() + 1,
        )
        chown_calls: list[tuple[Path, int, int]] = []

        def record_chown(path: Path, user_id: int, group_id: int) -> None:
            chown_calls.append((path, user_id, group_id))

        def assert_home_was_owned(username: str) -> None:
            assert username == "alice"
            assert chown_calls == [(home_path, user_record.pw_uid, user_record.pw_gid)]

        with (
            patch.object(normalize_forgejo_git_credentials, "HOME_ROOT", home_root),
            patch.object(
                normalize_forgejo_git_credentials.pwd,
                "getpwnam",
                return_value=user_record,
            ),
            patch.object(normalize_forgejo_git_credentials.os, "chown", side_effect=record_chown),
            patch.object(
                normalize_forgejo_git_credentials,
                "generate_token",
                side_effect=assert_home_was_owned,
            ),
        ):
            assert (
                normalize_forgejo_git_credentials.configure_git_credentials(
                    "https://forgejo.example",
                    "alice",
                )
                is False
            )

        assert home_path.stat().st_mode & 0o777 == 0o711
        assert not (home_path / ".config").exists()


def test_repair_changes_only_home_root_without_generating_token() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        home_root = Path(temporary_directory) / "home"
        home_root.mkdir()
        home_path = home_root / "alice"
        home_path.mkdir()
        learner_file = home_path / "keep-me.txt"
        learner_file.write_text("keep", encoding="utf-8")
        user_record = SimpleNamespace(
            pw_name="alice",
            pw_dir=str(home_path),
            pw_uid=os.getuid(),
            pw_gid=os.getgid() + 1,
        )

        with (
            patch.object(normalize_forgejo_git_credentials, "HOME_ROOT", home_root),
            patch.object(
                normalize_forgejo_git_credentials.pwd,
                "getpwnam",
                return_value=user_record,
            ),
            patch.object(normalize_forgejo_git_credentials.os, "chown") as chown,
            patch.object(
                normalize_forgejo_git_credentials,
                "generate_token",
                side_effect=AssertionError("repair must not generate tokens"),
            ),
        ):
            assert normalize_forgejo_git_credentials.repair_home_ownership("alice") is True

        assert chown.call_args_list == [((home_path, user_record.pw_uid, user_record.pw_gid),)]
        assert learner_file.read_text(encoding="utf-8") == "keep"


def test_repair_rejects_home_outside_home_root() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary_path = Path(temporary_directory)
        home_root = temporary_path / "home"
        home_root.mkdir()
        outside_home = temporary_path / "outside"
        outside_home.mkdir()
        user_record = SimpleNamespace(
            pw_name="alice",
            pw_dir=str(outside_home),
            pw_uid=os.getuid(),
            pw_gid=os.getgid(),
        )

        with (
            patch.object(normalize_forgejo_git_credentials, "HOME_ROOT", home_root),
            patch.object(
                normalize_forgejo_git_credentials.pwd,
                "getpwnam",
                return_value=user_record,
            ),
            patch.object(normalize_forgejo_git_credentials.os, "chown") as chown,
        ):
            try:
                normalize_forgejo_git_credentials.repair_home_ownership("alice")
            except ValueError as error:
                assert "unexpected home path" in str(error)
            else:
                raise AssertionError("unsafe home path was accepted")

        assert chown.call_count == 0


if __name__ == "__main__":
    test_configure_owns_absent_home_before_generating_token()
    test_repair_changes_only_home_root_without_generating_token()
    test_repair_rejects_home_outside_home_root()
