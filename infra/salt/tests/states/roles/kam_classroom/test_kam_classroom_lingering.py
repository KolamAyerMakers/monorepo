"""Behavioral coverage for the root-only course lingering reconciler."""

from __future__ import annotations

import grp
import importlib.util
import json
import pwd
import subprocess
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock

import pytest

from tests.support.paths import SALTSTACK_DIRECTORY


def _load_script() -> ModuleType:
    specification = importlib.util.spec_from_file_location(
        "kam_classroom_lingering",
        SALTSTACK_DIRECTORY
        / "states/roles/kam-classroom/files/kam_classroom_lingering.py",
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@pytest.mark.parametrize("disable", [False, True])
@pytest.mark.parametrize("username", [None, "alice"])
def test_reconciles_only_policy_members_idempotently(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    disable: bool,
    username: str | None,
) -> None:
    """Both mentors and learners resolve directly, without NSS enumeration."""
    script = _load_script()
    policy = tmp_path / "policy"
    _ = policy.write_text(
        json.dumps(
            {"group": "course-participants", "uid_minimum": 10000, "uid_maximum": 20999}
        ),
        encoding="utf-8",
    )
    markers = tmp_path / "linger"
    markers.mkdir()
    (markers / "outsider").touch()
    accounts = {
        "alice": pwd.struct_passwd(
            ("alice", "x", 20999, 1001, "", "/home/alice", "/bin/bash")
        ),
        "mentor": pwd.struct_passwd(
            ("mentor", "x", 10000, 1001, "", "/home/mentor", "/bin/bash")
        ),
    }
    if disable:
        for name in accounts:
            (markers / name).touch()
    calls: list[list[str]] = []

    def account_by_id(user_id: int) -> pwd.struct_passwd:
        return next(
            account for account in accounts.values() if account.pw_uid == user_id
        )

    def run(command: list[str], *, check: bool) -> subprocess.CompletedProcess[str]:
        assert check is True
        calls.append(command)
        if command[0] == "/usr/sbin/sss_cache":
            assert command == ["/usr/sbin/sss_cache", "-g", "course-participants"]
        else:
            assert command[:3] == [
                "/usr/bin/loginctl",
                "disable-linger" if disable else "enable-linger",
                "--",
            ]
            if disable:
                (markers / command[-1]).unlink()
            else:
                (markers / command[-1]).touch()
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(script, "POLICY_FILE", policy)
    monkeypatch.setattr(script, "LINGER_DIRECTORY", markers)
    monkeypatch.setattr(script.os, "geteuid", lambda: 0)
    monkeypatch.setattr(
        script.grp,
        "getgrnam",
        Mock(
            return_value=grp.struct_group(
                ("course-participants", "x", 1012, list(accounts))
            )
        ),
    )
    monkeypatch.setattr(script.pwd, "getpwnam", accounts.__getitem__)
    monkeypatch.setattr(script.pwd, "getpwuid", account_by_id)
    monkeypatch.setattr(
        script.pwd, "getpwall", Mock(side_effect=AssertionError("enumeration"))
    )
    monkeypatch.setattr(script.subprocess, "run", run)
    arguments = (["--disable"] if disable else []) + ([username] if username else [])

    assert script.main(arguments) == 0
    assert json.loads(capsys.readouterr().out)["changed"] is True
    assert [command[-1] for command in calls if command[0] == "/usr/bin/loginctl"] == (
        [username] if username else ["alice", "mentor"]
    )
    calls.clear()
    assert script.main(arguments) == 0
    assert json.loads(capsys.readouterr().out)["changed"] is False
    assert calls == [["/usr/sbin/sss_cache", "-g", "course-participants"]]
    assert script.main(["--disable", "outsider"]) == 0
    assert json.loads(capsys.readouterr().out)["changed"] is False
    assert (markers / "outsider").exists()


@pytest.mark.parametrize(
    ("failure", "user_id", "expected_error", "error_message"),
    [
        ("unprivileged", 20002, PermissionError, "must run as root"),
        ("range", 20002, ValueError, "invalid lingering policy UID range"),
        ("missing", 20002, KeyError, "bob"),
        ("uid", 0, ValueError, "unsafe participant identity: bob"),
        ("uid", 1000, ValueError, "unsafe participant identity: bob"),
        ("uid", 9999, ValueError, "unsafe participant identity: bob"),
        ("uid", 21000, ValueError, "unsafe participant identity: bob"),
        ("alias", 20002, ValueError, "unsafe participant identity: bob"),
        ("home", 20002, ValueError, "unsafe participant identity: bob"),
        ("cache", 20002, subprocess.CalledProcessError, "sss_cache"),
        ("outside", 20002, ValueError, "not in lingering policy group: outsider"),
    ],
)
def test_fails_before_lingering_mutation_on_unsafe_resolution(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    failure: str,
    user_id: int,
    expected_error: type[Exception],
    error_message: str,
) -> None:
    """Unknown or unsafe members fail closed, including partial NSS failures."""
    script = _load_script()
    policy = tmp_path / "policy"
    _ = policy.write_text(
        json.dumps(
            {
                "group": "course-participants",
                "uid_minimum": 21000 if failure == "range" else 10000,
                "uid_maximum": 20999,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(script, "POLICY_FILE", policy)
    monkeypatch.setattr(script, "LINGER_DIRECTORY", tmp_path / "linger")
    monkeypatch.setattr(
        script.os, "geteuid", lambda: 1000 if failure == "unprivileged" else 0
    )
    monkeypatch.setattr(
        script.grp,
        "getgrnam",
        Mock(
            return_value=grp.struct_group(
                ("course-participants", "x", 1012, ["alice", "bob"])
            )
        ),
    )

    accounts = {
        "alice": pwd.struct_passwd(
            ("alice", "x", 20001, 1001, "", "/home/alice", "/bin/bash")
        ),
        "bob": pwd.struct_passwd(
            (
                "bob",
                "x",
                user_id,
                1001,
                "",
                "/root" if failure == "home" else "/home/bob",
                "/bin/bash",
            )
        ),
    }

    def account_by_name(username: str) -> pwd.struct_passwd:
        if username == "bob" and failure == "missing":
            raise KeyError(username)
        return accounts[username]

    def account_by_id(resolved_user_id: int) -> pwd.struct_passwd:
        if resolved_user_id == user_id and failure == "alias":
            return accounts["alice"]
        return next(
            account
            for account in accounts.values()
            if account.pw_uid == resolved_user_id
        )

    def run(command: list[str], *, check: bool) -> subprocess.CompletedProcess[str]:
        assert command[0] == "/usr/sbin/sss_cache"
        assert check is True
        if failure == "cache":
            raise subprocess.CalledProcessError(1, command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(script.pwd, "getpwnam", account_by_name)
    monkeypatch.setattr(script.pwd, "getpwuid", account_by_id)
    monkeypatch.setattr(script.subprocess, "run", run)
    with pytest.raises(expected_error, match=error_message):
        script.main(["outsider"] if failure == "outside" else [])
