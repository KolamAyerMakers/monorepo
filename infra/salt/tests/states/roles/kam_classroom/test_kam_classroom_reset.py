"""Tests for the destructive classroom reset helper."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import grp
import pwd
import sqlite3
import subprocess
from collections.abc import Callable, Iterable
from pathlib import Path
from types import ModuleType

import pytest

from tests.support.paths import SALTSTACK_DIRECTORY


def _load_script() -> ModuleType:
    loader = importlib.machinery.SourceFileLoader(
        "kam_classroom_reset",
        str(
            SALTSTACK_DIRECTORY
            / "states/roles/kam-classroom/files/kam_classroom_reset.py"
        ),
    )
    specification = importlib.util.spec_from_loader(loader.name, loader)
    if specification is None:
        raise AssertionError("Could not load kam-classroom-reset script")
    module = importlib.util.module_from_spec(specification)
    loader.exec_module(module)
    return module


def test_learner_requires_an_exact_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A mismatched learner confirmation cannot reach mutation code."""
    script = _load_script()
    monkeypatch.setattr(script, "_validate_learner", _validate_learner)
    monkeypatch.setattr(script, "_run_commands", _run_commands)

    with pytest.raises(script.ResetError, match="exactly match"):
        script._reset_learner("alice", "bob", True)


def test_all_requires_the_fixed_confirmation() -> None:
    """The broad reset cannot run from a copied learner confirmation."""
    script = _load_script()

    with pytest.raises(script.ResetError, match="RESET-LEARNING-ENVIRONMENT"):
        script._reset_all("alice", True)


def test_all_reset_removes_snapshotted_homes_and_requires_controller_reapply(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """The all reset removes homes before dropping the identity provider."""
    script = _load_script()
    commands: list[tuple[str, ...]] = []
    removed_paths: list[Path] = []
    kam_registration_cache = tmp_path / "kam-registration"
    kam_registration_cache.mkdir()
    kam_classroom_cache = tmp_path / "kam-classroom"
    kam_classroom_cache.mkdir()
    monkeypatch.setattr(script, "_learner_usernames", lambda: ("alice",))
    monkeypatch.setattr(script, "_run_commands", _record_commands(commands))
    monkeypatch.setattr(script, "_remove_path", removed_paths.append)
    monkeypatch.setattr(script, "VAR_LIB_ROOT", tmp_path)

    script._reset_all(script.CONFIRM_ALL, True)

    assert commands == [
        ("/usr/bin/loginctl", "terminate-user", "alice"),
        ("/usr/bin/systemctl", "stop", "maker-guide-sync-derived-data.timer"),
        ("/usr/bin/systemctl", "stop", "maker-guide-bot.service"),
        ("/usr/bin/systemctl", "stop", "forgejo.service"),
        ("/usr/bin/systemctl", "stop", "ergo.service"),
        ("/usr/bin/systemctl", "stop", "authelia.service"),
        ("/usr/bin/systemctl", "stop", "lldap.service"),
        ("/usr/sbin/sss_cache", "-E"),
    ]
    assert removed_paths == [
        Path("/home/alice"),
        script.DATABASE_PATH,
        script.DATABASE_PATH.with_name(f"{script.DATABASE_PATH.name}-shm"),
        script.DATABASE_PATH.with_name(f"{script.DATABASE_PATH.name}-wal"),
        script.AUDIT_ROOT,
        Path("/var/lib/maker-guide/shiv"),
        Path("/var/lib/maker-guide/.shiv"),
        Path("/root/.shiv"),
        kam_classroom_cache,
        kam_registration_cache,
        script.MAKERS_ROOT,
        script.DOCUMENTS_OUTPUT,
        script.LEARNER_ROUTES_PATH,
        Path("/data/lldap"),
        Path("/data/forgejo"),
        Path("/data/ergo"),
        Path("/data/authelia"),
    ]
    assert "ssh-apply <classroom-host> roles.kam-classroom" in capsys.readouterr().out


def test_learner_usernames_resolves_classroom_members_directly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SSSD disables enumeration, so reset resolves each group member by name."""
    script = _load_script()
    accounts = {
        "alice": _account("alice", 20_001, "/home/alice"),
        "guide": _account("guide", 20_002, "/home/guide"),
        "outsider": _account("outsider", 19_999, "/home/outsider"),
        "unsafe": _account("unsafe", 20_003, "/srv/unsafe"),
    }

    def classroom_group(group_name: str) -> grp.struct_group:
        assert group_name == "lf2607"
        return _group(accounts)

    monkeypatch.setattr(script.grp, "getgrnam", classroom_group)
    monkeypatch.setattr(script.pwd, "getpwnam", accounts.__getitem__)

    assert script._learner_usernames() == ("alice",)


def test_learner_restart_runs_after_a_failed_deletion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed deletion does not leave the teaching bot stopped."""
    script = _load_script()
    calls: list[str] = []
    monkeypatch.setattr(script, "_validate_learner", _validate_learner)
    monkeypatch.setattr(script, "_learner_stop_commands", _stop_commands)
    monkeypatch.setattr(script, "_learner_mutation_commands", _mutation_commands)
    monkeypatch.setattr(script, "_learner_start_commands", _start_commands)
    monkeypatch.setattr(script, "_run_commands", _failing_run_commands(calls))

    with pytest.raises(subprocess.CalledProcessError):
        script._reset_learner("alice", "alice", True)

    assert calls == ["stop", "delete", "start"]


def test_terminate_user_ignores_an_absent_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Removing a user without a logind session remains safe to repeat."""
    script = _load_script()
    commands: list[tuple[str, ...]] = []

    def run(
        command: tuple[str, ...], *, capture_output: bool, text: bool
    ) -> subprocess.CompletedProcess[str]:
        assert capture_output is True
        assert text is True
        commands.append(command)
        return subprocess.CompletedProcess(
            command,
            1,
            stderr="Could not terminate user: User ID 20001 is not logged in or lingering\n",
        )

    monkeypatch.setattr(script.subprocess, "run", run)

    script._run_commands((("/usr/bin/loginctl", "terminate-user", "alice"),))

    assert commands == [("/usr/bin/loginctl", "terminate-user", "alice")]


def test_learner_database_cleanup_removes_state_and_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Learner cleanup removes direct state, audit rows, and matching outbox work."""
    script = _load_script()
    database_path = tmp_path / "state.db"
    with sqlite3.connect(database_path) as database_connection:
        _ = database_connection.execute(
            "create table learners (handle text primary key)"
        )
        _ = database_connection.execute("create table audit_events (handle text)")
        _ = database_connection.execute("create table outbox_items (payload_json text)")
        _ = database_connection.execute("insert into learners values ('alice')")
        _ = database_connection.execute("insert into learners values ('bob')")
        _ = database_connection.execute("insert into audit_events values ('alice')")
        _ = database_connection.execute("insert into audit_events values ('bob')")
        _ = database_connection.execute(
            'insert into outbox_items values (\'{"handle":"alice"}\')'
        )
        _ = database_connection.execute(
            'insert into outbox_items values (\'{"handle":"bob"}\')'
        )
    monkeypatch.setattr(script, "DATABASE_PATH", database_path)

    script._delete_learner_database_data("alice")

    with sqlite3.connect(database_path) as database_connection:
        assert database_connection.execute(
            "select handle from learners"
        ).fetchall() == [("bob",)]
        assert database_connection.execute(
            "select handle from audit_events"
        ).fetchall() == [("bob",)]
        assert database_connection.execute(
            "select payload_json from outbox_items"
        ).fetchall() == [('{"handle":"bob"}',)]


def test_audit_scrub_removes_matching_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scrubbing rewrites shared audit files without the learner's records."""
    script = _load_script()
    audit_path = tmp_path / "audit" / "2026-07-17.jsonl"
    audit_path.parent.mkdir()
    _ = audit_path.write_text(
        '{"handle":"alice"}\n{"handle":"bob"}\n', encoding="utf-8"
    )
    monkeypatch.setattr(script, "AUDIT_ROOT", audit_path.parent)

    script._scrub_audit_exports("alice")

    assert audit_path.read_text(encoding="utf-8") == '{"handle":"bob"}\n'


def _validate_learner(username: str) -> None:
    del username


def _run_commands(commands: Iterable[tuple[str, ...]]) -> None:
    del commands


def _stop_commands() -> tuple[tuple[str, ...], ...]:
    return (("stop",),)


def _mutation_commands(username: str) -> tuple[tuple[str, ...], ...]:
    del username
    return (("delete",),)


def _start_commands() -> tuple[tuple[str, ...], ...]:
    return (("start",),)


def _failing_run_commands(
    calls: list[str],
) -> Callable[[Iterable[tuple[str, ...]]], None]:
    def run_commands(commands: Iterable[tuple[str, ...]]) -> None:
        command = next(iter(commands))
        calls.append(command[0])
        if command[0] == "delete":
            raise subprocess.CalledProcessError(1, command)

    return run_commands


def _record_commands(
    commands: list[tuple[str, ...]],
) -> Callable[[Iterable[tuple[str, ...]]], None]:
    def run_commands(command_batch: Iterable[tuple[str, ...]]) -> None:
        commands.extend(command_batch)

    return run_commands


def _account(username: str, user_id: int, home_directory: str) -> pwd.struct_passwd:
    return pwd.struct_passwd(
        (username, "x", user_id, user_id, "", home_directory, "/bin/bash")
    )


def _group(accounts: dict[str, pwd.struct_passwd]) -> grp.struct_group:
    return grp.struct_group(("lf2607", "x", 1007, list(accounts)))
