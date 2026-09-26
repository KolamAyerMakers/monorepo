"""Exercise real private files while replacing every systemd/HTTP subprocess."""

# ruff: noqa: SLF001
# pyright: reportPrivateUsage=false

from __future__ import annotations

import errno
import fcntl
import os
import pwd
import stat
from collections.abc import Generator
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import cast

import pytest

from maker_guide.cli import service_lab as runner
from maker_guide.service_lab import (
    SERVICE_LAB_SCENARIOS,
    ServiceLabAction,
    ServiceLabError,
    ServiceLabScenario,
    service_lab_report_payload,
)


@dataclass(frozen=True, kw_only=True, slots=True)
class _Machine:
    home: Path
    original: bytes
    commands: list[tuple[str, ...]] = field(default_factory=list)
    state: dict[str, str] = field(default_factory=dict)

    @property
    def unit(self) -> Path:
        return self.home / ".config/systemd/user/site.service"

    def repair(self) -> None:
        """Simulate the learner editing, reloading and restarting the course unit."""
        self.unit.write_bytes(self.original)
        self.state.update(loaded=self.original.decode(), ActiveState="active", SubState="running")

    def rebuild(self) -> None:
        """Regenerate output without touching the running service or the source tree."""
        (self.home / "public_html").mkdir(exist_ok=True)
        (self.home / "public_html/index.html").write_bytes(b"rebuilt real homepage\n")

    def command(  # noqa: C901, PLR0911, PLR0912 - one subprocess boundary for the fake user manager
        self,
        arguments: tuple[str, ...],
        environment: dict[str, str],
        _deadline: float,
        _limit: int = 32768,
    ) -> tuple[int, bytes]:
        """Respond to fixed local argv without ever invoking the real user manager."""
        self.commands.append(arguments)
        assert environment["HOME"] == str(self.home)
        assert environment["DBUS_SESSION_BUS_ADDRESS"] == f"unix:path=/run/user/{os.getuid()}/bus"
        assert environment["XDG_RUNTIME_DIR"] == f"/run/user/{os.getuid()}"
        assert "LD_PRELOAD" not in environment
        assert "SYSTEMD_UNIT_PATH" not in environment
        assert "http_proxy" not in environment
        assert "DBUS_SYSTEM_BUS_ADDRESS" not in environment
        if arguments[0] == "/usr/bin/curl":
            assert arguments[1] == "-q"
            assert arguments[-1] == f"http://127.0.0.1:{10000 + os.getuid()}/"
            assert "--location" not in arguments
            assert arguments[arguments.index("--noproxy") + 1] == "*"
            if self.state["ActiveState"] != "active":
                return 7, b"\n000"
            if self.state.get("bad-http"):
                return 0, b"unrelated page\n200"
            if self.state.get("unwitnessed"):
                return 0, b"current real homepage\n\n200"
            command = runner._settings(self.state["loaded"].encode())["[Service]ExecStart"].split()
            root = Path(command[command.index("--root") + 1].replace("%h", str(self.home)))
            try:
                return 0, (root / "index.html").read_bytes() + b"\n200"
            except FileNotFoundError:
                return 0, b"\n404"
        if arguments[0] == "/usr/bin/journalctl":
            assert "--unit=site.service" in arguments
            return 0, self.state.get("journal", "bounded local service journal\n").encode()
        assert arguments[:4] == ("/usr/bin/systemctl", "--user", "--no-pager", "--no-ask-password")
        operation = arguments[4:]
        if operation[0] == "show":
            assert operation[1] == "site.service"
            assert "--all" in operation
            return 0, self.properties()
        if operation == ("show-environment",):
            return 0, self.state.get(
                "manager-environment",
                "\n".join(
                    (
                        f"HOME={self.home}",
                        f"USER={environment['USER']}",
                        "PATH=/usr/bin:/bin",
                        "LANG=C.UTF-8",
                        f"XDG_RUNTIME_DIR={environment['XDG_RUNTIME_DIR']}",
                        "",
                    )
                ),
            ).encode()
        if operation == ("daemon-reload",):
            if self.state.pop("interrupt", ""):
                raise KeyboardInterrupt
            if self.state.pop("fail-reload", ""):
                if self.state.get("concurrent-edit"):
                    self.unit.write_text("learner's unrelated edit\n", encoding="utf-8")
                raise ServiceLabError("runner-unavailable")
            self.state["loaded"] = self.unit.read_text(encoding="utf-8")
        elif operation == ("--no-block", "restart", "site.service"):
            self.state["ExecMainStartTimestampMonotonic"] = str(
                int(self.state["ExecMainStartTimestampMonotonic"]) + 1
            )
            failure = next(
                (
                    code
                    for token, code in (
                        ("/usr/bin/cadddyyy", "203"),
                        ("missing-caddy", "203"),
                        ("--access-logs", "1"),
                    )
                    if token in self.state["loaded"]
                ),
                None,
            )
            self.state.update(
                ActiveState="failed" if failure else "active",
                SubState="failed" if failure else "running",
                Result="exit-code" if failure else "success",
                ExecMainCode="1" if failure else "0",
                ExecMainStatus="2" if self.state.get("unwitnessed") else failure or "0",
            )
        else:
            assert operation == ("reset-failed", "site.service")
        return 0, b""

    def properties(self) -> bytes:
        """Expose independently loaded properties, including stale-file detection."""
        settings = dict(
            line.split("=", 1)
            for line in self.state["loaded"].replace("\\\n", " ").splitlines()
            if "=" in line
        )
        command = " ".join(settings["ExecStart"].replace("%h", str(self.home)).split())
        properties: dict[str, str] = dict.fromkeys(runner._PROPERTIES, "")
        properties.update(
            Id="site.service",
            Names="site.service",
            LoadState="loaded",
            FragmentPath=str(self.unit),
            NeedDaemonReload=(
                "no" if self.unit.read_text(encoding="utf-8") == self.state["loaded"] else "yes"
            ),
            Transient="no",
            Type="simple",
            Restart="on-failure",
            WorkingDirectory=settings["WorkingDirectory"].replace("%h", str(self.home)),
            ExecStart="".join(
                (
                    f"{{ path={command.split()[0]} ; argv[]={command} ; ignore_errors=no ; ",
                    "start_time=n/a ; stop_time=n/a ; pid=123 ; code=(null) ; status=0/0 }",
                )
            ),
        )
        properties.update((name, value) for name, value in self.state.items() if name in properties)
        if missing := self.state.get("missing-property"):
            properties.pop(missing)
        # Ubuntu's systemctl omits these empty structured arrays even with --all.
        for name in (
            "EnvironmentFiles",
            "ExecStartPre",
            "ExecStartPost",
            "ExecStop",
            "ExecStopPost",
            "ExecReload",
            "ExecCondition",
        ):
            if properties.get(name) == "":
                properties.pop(name)
        return "\n".join(f"{name}={value}" for name, value in properties.items()).encode()


@pytest.fixture(autouse=True)
def private_file_creation() -> Generator[None]:
    """Create valid private learner files regardless of the invoking shell's umask."""
    previous = os.umask(0o077)
    try:
        yield
    finally:
        os.umask(previous)


@pytest.fixture
def machine(
    temporary_path: Path, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> _Machine:
    """Mock only account home and subprocesses; retain real file/UID protections."""
    if os.getuid() == 0 or os.getuid() > 55535:
        pytest.skip("File-safety tests require a real non-root UID with an assigned course port")
    account = pwd.getpwuid(os.getuid())

    def learner_account(_user_id: int) -> pwd.struct_passwd:
        return pwd.struct_passwd(
            (
                account.pw_name,
                "x",
                account.pw_uid,
                account.pw_gid,
                "",
                str(temporary_path),
                "/bin/bash",
            )
        )

    monkeypatch.setattr(runner.pwd, "getpwuid", learner_account)

    def wrong_root(action: ServiceLabAction) -> Path:
        return temporary_path / f"guide-{os.getuid()}-{action.run_id}"

    monkeypatch.setattr(runner, "_wrong_root", wrong_root)
    (temporary_path / ".config/systemd/user").mkdir(parents=True)
    (temporary_path / "public_html").mkdir()
    (temporary_path / "public_html/index.html").write_bytes(b"current real homepage\n")
    (temporary_path / "public_html/assets").mkdir()
    (temporary_path / "public_html/assets/site.css").write_bytes(b"generated stylesheet\n")
    (temporary_path / "src/website").mkdir(parents=True)
    (temporary_path / "src/website/source.astro").write_bytes(b"learner source\n")
    fixture = _Machine(
        home=temporary_path,
        original="".join(
            (
                "[Unit]\nDescription=Personal website service\n\n[Service]\nWorkingDirectory=%h\n",
                f"ExecStart=/usr/bin/caddy file-server --listen :{10000 + os.getuid()} ",
                "--root %h/public_html --access-log\nRestart=on-failure\n\n",
                "[Install]\nWantedBy=default.target\n",
            )
        ).encode(),
    )
    unit_format = cast("object", getattr(request, "param", "single-line"))
    if unit_format == "multiline":
        fixture = replace(
            fixture,
            original=fixture.original.replace(b"file-server ", b"file-server \\\n  ").replace(
                b" --access-log", b" \\\n  --access-log"
            ),
        )
    elif unit_format == "no-description":
        fixture = replace(
            fixture,
            original=fixture.original.replace(b"Description=Personal website service\n", b""),
        )
    fixture.repair()
    fixture.state.update(
        ExecMainStartTimestampMonotonic="1", ExecMainStatus="0", ExecMainCode="0", MainPID="123"
    )
    monkeypatch.setattr(runner, "_command", fixture.command)

    def running_process(_source: bytes, home: Path, _properties: dict[str, str]) -> None:
        assert home == fixture.home
        if fixture.state.get("unsafe-process"):
            raise ServiceLabError("unsafe-unit")

    monkeypatch.setattr(runner, "_running_process", running_process)
    for variable in (
        "HOME",
        "LD_PRELOAD",
        "SYSTEMD_UNIT_PATH",
        "http_proxy",
        "DBUS_SYSTEM_BUS_ADDRESS",
    ):
        monkeypatch.setenv(variable, "untrusted-caller-value")
    return fixture


@pytest.mark.parametrize("machine", ["single-line", "multiline", "no-description"], indirect=True)
@pytest.mark.parametrize("scenario", SERVICE_LAB_SCENARIOS)
def test_injection_repair_and_retry_are_exactly_once(  # noqa: PLR0915 - shared lifecycle regression
    machine: _Machine, scenario: ServiceLabScenario
) -> None:
    """A lost reply or repaired retry never creates another fault for the same run."""
    action = ServiceLabAction(run_id="a" * 32, scenario=scenario, operation="start")
    published = (machine.home / "public_html").stat()
    unit = machine.unit.stat()
    report = runner.run_service_lab(action)
    assert report.error is None
    assert report.started
    assert not report.healthy
    service_lab_report_payload(report)
    assert report.http_status == (
        200
        if scenario == "wrong-content"
        else 404
        if scenario in {"empty-root", "missing-published-site"}
        else None
    )
    injected = machine.unit.read_bytes()
    assert (injected == machine.original) == (scenario == "missing-published-site")
    if scenario == "empty-root":
        assert f"--root {machine.home / 'empty-site'} --access-log" in " ".join(
            runner._settings(report.unit.encode())["[Service]ExecStart"].split()
        )
        assert not list((machine.home / "empty-site").iterdir())
    if scenario == "missing-executable":
        assert b"ExecStart=/usr/bin/cadddyyy file-server" in injected
        assert "ExecMainStatus=203" in report.status
    if scenario == "invalid-argument":
        assert b"ExecStart=/usr/bin/caddy file-server" in injected
        assert b"WorkingDirectory=%h\n" in injected
        assert b"--access-logs" in injected
        assert "ExecMainStatus=1" in report.status
    attempt = machine.home / runner._STATE / action.run_id
    assert (attempt / "original.service").read_bytes() == machine.original
    assert (attempt.stat().st_mode & 0o777) == 0o700
    if scenario == "missing-published-site":
        assert not (machine.home / "public_html").exists()
        backup = next(attempt.glob("published-*"))
        assert (backup.stat().st_dev, backup.stat().st_ino) == (published.st_dev, published.st_ino)
        assert (backup / "index.html").read_bytes() == b"current real homepage\n"
        assert (backup / "assets/site.css").read_bytes() == b"generated stylesheet\n"
        assert machine.unit.stat().st_ino == unit.st_ino
        assert machine.unit.stat().st_mtime_ns == unit.st_mtime_ns
        assert machine.state["ExecMainStartTimestampMonotonic"] == "1"
        assert machine.state["MainPID"] == "123"
        assert not any(
            operation in command
            for command in machine.commands
            for operation in ("restart", "daemon-reload", "reset-failed")
        )
    else:
        assert (machine.home / "public_html/index.html").read_bytes() == b"current real homepage\n"
    if scenario == "wrong-content":
        assert str(runner._wrong_root(action)).encode() in injected
        assert not runner._wrong_root(action).is_relative_to(attempt)
        assert (runner._wrong_root(action).stat().st_mode & 0o777) == 0o700
        assert (runner._wrong_root(action) / "index.html").read_bytes() == runner._WRONG_INDEX
    assert (machine.home / "src/website/source.astro").read_bytes() == b"learner source\n"
    count = len(machine.commands)
    report = runner.run_service_lab(action)
    assert report.started
    assert not report.healthy
    assert machine.unit.read_bytes() == injected
    assert not any("restart" in command for command in machine.commands[count:])
    machine.repair()
    if scenario == "missing-published-site":
        machine.state["ExecMainStartTimestampMonotonic"] = "2"
        report = runner.run_service_lab(replace(action, operation="inspect"))
        assert report.started
        assert not report.healthy
        assert report.error is None
        assert report.http_status == 404
        assert report.journal
        machine.rebuild()
        published = (machine.home / "public_html").stat()
    report = runner.run_service_lab(replace(action, operation="inspect"))
    assert report.started
    assert report.healthy
    assert report.error is None
    count = len(machine.commands)
    assert runner.run_service_lab(action).healthy
    assert machine.unit.read_bytes() == machine.original
    assert not any("restart" in command for command in machine.commands[count:])
    if scenario == "missing-published-site":
        assert (machine.home / "public_html").stat().st_ino == published.st_ino
        assert machine.state["ExecMainStartTimestampMonotonic"] == "2"
    machine.state["bad-http"] = "yes"
    assert not runner.run_service_lab(replace(action, operation="inspect")).healthy
    machine.state.pop("bad-http")
    assert runner.run_service_lab(replace(action, run_id="b" * 32)).started
    assert (attempt / "original.service").read_bytes() == machine.original


@pytest.mark.parametrize(
    ("state_name", "value"),
    [
        ("missing-property", "FragmentPath"),
        ("missing-property", "DropInPaths"),
        ("missing-property", "Environment"),
        ("missing-property", "ExecStart"),
        ("missing-property", "MainPID"),
        ("EnvironmentFiles", "/unrecognized/override"),
        ("ExecStartPre", "/unrecognized/override"),
        ("ExecCondition", "/unrecognized/override"),
        ("manager-environment", "LD_PRELOAD=/untrusted/library.so"),
        ("manager-environment", "CADDY_ADMIN=other:2019"),
        ("manager-environment", "HOME=/another/account"),
    ],
)
def test_unsafe_manager_state_cannot_reach_restart(
    machine: _Machine, state_name: str, value: str
) -> None:
    """Missing safety evidence and extra commands or environment must all fail closed."""
    machine.state[state_name] = value
    report = runner.run_service_lab(
        ServiceLabAction(run_id="a" * 32, scenario="empty-root", operation="start")
    )
    assert report.error == "unsafe-unit"
    assert not report.started
    assert machine.unit.read_bytes() == machine.original
    assert not any("daemon-reload" in command for command in machine.commands)


@pytest.mark.parametrize("machine", ["single-line", "multiline"], indirect=True)
@pytest.mark.parametrize("unsafe", ["continued-command", "comment-backslash", "dangling"])
def test_continuations_do_not_hide_unrecognized_directives(machine: _Machine, unsafe: str) -> None:
    """Join only continuation lines, without treating a comment's backslash as syntax."""
    if unsafe == "continued-command":
        source = machine.original.replace(
            b"--access-log", b"--access-log \\\nExecStartPre=/usr/bin/true"
        )
    elif unsafe == "comment-backslash":
        source = machine.original.replace(
            b"[Install]", b"# comment \\\nExecStartPre=/usr/bin/true\n[Install]"
        )
    else:
        source = machine.original + b"\\\n"
    machine.unit.write_bytes(source)
    report = runner.run_service_lab(
        ServiceLabAction(run_id="a" * 32, scenario="empty-root", operation="start")
    )
    assert report.error == "unsafe-unit"
    assert not report.started
    assert machine.unit.read_bytes() == source
    assert not any("daemon-reload" in command for command in machine.commands)


@pytest.mark.parametrize(
    "unsafe",
    [
        "custom",
        "wrong-port",
        "extra-command",
        "environment",
        "unit-symlink",
        "hardlink",
        "unit-permissions",
        "parent-symlink",
        "index-symlink",
        "published-symlink",
        "published-permissions",
        "fragment",
        "drop-in",
        "runtime-environment",
        "loaded-command",
        "stale-unit",
        "old-process",
    ],
)
def test_unsafe_baselines_are_never_modified(  # noqa: C901, PLR0912 - refusal matrix
    machine: _Machine, unsafe: str
) -> None:
    """Source, installed properties, regular files and every directory must agree."""
    if unsafe == "custom":
        machine.unit.write_bytes(machine.original.replace(b"/usr/bin/caddy", b"/usr/bin/other"))
    elif unsafe == "wrong-port":
        machine.unit.write_bytes(
            machine.original.replace(f":{10000 + os.getuid()}".encode(), b":8000")
        )
    elif unsafe in {"extra-command", "environment"}:
        machine.unit.write_bytes(
            machine.original.replace(
                b"Restart=on-failure",
                b"Restart=on-failure\n"
                + (
                    b"ExecStartPre=/usr/bin/true"
                    if unsafe == "extra-command"
                    else b"Environment=A=B"
                ),
            )
        )
    elif unsafe in {"unit-symlink", "hardlink"}:
        saved = machine.home / "saved-unit"
        machine.unit.rename(saved)
        if unsafe == "unit-symlink":
            machine.unit.symlink_to(saved)
        else:
            machine.unit.hardlink_to(saved)
    elif unsafe == "unit-permissions":
        machine.unit.chmod(0o666)
    elif unsafe == "parent-symlink":
        saved = machine.home / "saved-directory"
        machine.unit.parent.rename(saved)
        machine.unit.parent.symlink_to(saved, target_is_directory=True)
    elif unsafe == "index-symlink":
        index = machine.home / "public_html/index.html"
        index.rename(machine.home / "private-index")
        index.symlink_to(machine.home / "private-index")
    elif unsafe == "published-symlink":
        (machine.home / "public_html").rename(machine.home / "saved-published")
        (machine.home / "public_html").symlink_to(
            machine.home / "src/website", target_is_directory=True
        )
    elif unsafe == "published-permissions":
        (machine.home / "public_html").chmod(0o777)
    elif unsafe == "fragment":
        machine.state["FragmentPath"] = str(machine.home / "other.service")
    elif unsafe == "drop-in":
        machine.state["DropInPaths"] = str(machine.home / "override.conf")
    elif unsafe == "runtime-environment":
        machine.state["Environment"] = "A=B"
    elif unsafe == "loaded-command":
        machine.state["ExecStart"] = "{ path=/usr/bin/other ; argv[]=/usr/bin/other ; }"
    elif unsafe == "old-process":
        machine.state["unsafe-process"] = "yes"
    else:
        machine.state["NeedDaemonReload"] = "yes"
    before = machine.unit.read_bytes()
    report = runner.run_service_lab(
        ServiceLabAction(
            run_id="a" * 32,
            scenario=(
                "missing-published-site"
                if unsafe.startswith("published-")
                else "missing-executable"
            ),
            operation="start",
        )
    )
    assert report.error is not None
    assert not report.started
    assert not report.healthy
    assert machine.unit.read_bytes() == before
    assert not any(
        "restart" in command or "daemon-reload" in command for command in machine.commands
    )
    assert (machine.home / "src/website/source.astro").read_bytes() == b"learner source\n"


@pytest.mark.parametrize("failure", ["inactive", "wrong-body"])
def test_unhealthy_baseline_and_inspect_do_not_inject(machine: _Machine, failure: str) -> None:
    """Inspection cannot start an attempt, and HTTP 200 alone is not healthy."""
    action = ServiceLabAction(run_id="a" * 32, scenario="empty-root", operation="inspect")
    assert runner.run_service_lab(action).error == "attempt-missing"
    if failure == "inactive":
        machine.state["ActiveState"] = "inactive"
    else:
        machine.state["bad-http"] = "yes"
    assert runner.run_service_lab(replace(action, operation="start")).error == "baseline-unhealthy"
    assert machine.unit.read_bytes() == machine.original
    assert not any("restart" in command for command in machine.commands)


def test_readonly_baseline_does_not_reserve_an_unusable_directory(machine: _Machine) -> None:
    """Correcting unit permissions is enough to retry the same run."""
    action = ServiceLabAction(run_id="a" * 32, scenario="missing-executable", operation="start")
    machine.unit.chmod(0o400)
    assert runner.run_service_lab(action).error == "unsafe-path"
    assert not (machine.home / runner._STATE / action.run_id).exists()
    assert not (machine.home / runner._STATE / "current").exists()
    assert machine.unit.read_bytes() == machine.original
    assert not any("restart" in command for command in machine.commands)
    machine.unit.chmod(0o600)
    assert runner.run_service_lab(action).started


@pytest.mark.parametrize(
    ("partial", "scenario"),
    [
        ("empty", "missing-executable"),
        ("original", "missing-executable"),
        ("injected", "invalid-argument"),
        ("empty-root", "empty-root"),
        ("wrong-root", "wrong-content"),
        ("wrong-index", "wrong-content"),
    ],
)
def test_partial_initialization_resumes_only_on_start_without_replacing_artifacts(
    machine: _Machine, partial: str, scenario: ServiceLabScenario
) -> None:
    """Reuse durable files and roots; leave unknown files and backups untouched."""
    action = ServiceLabAction(run_id="a" * 32, scenario=scenario, operation="start")
    attempt = machine.home / runner._STATE / action.run_id
    attempt.mkdir(parents=True, mode=0o700)
    attempt.parent.chmod(0o700)
    if partial != "empty":
        (attempt / "original.service").write_bytes(machine.original)
        (attempt / "original.service").chmod(machine.unit.stat().st_mode & 0o777)
        (attempt / "retained-backup").mkdir()
        (attempt / "retained-backup/site.service").write_bytes(b"unrelated retained edit\n")
        (attempt / ".write-unfinished").write_bytes(b"unfinished private write\n")
    if partial not in {"empty", "original"}:
        (attempt / "injected.service").write_bytes(
            runner._fault(machine.original, action, attempt)[0]
        )
        (attempt / "injected.service").chmod(0o600)
    if partial == "empty-root":
        (attempt / "empty-root").mkdir(mode=0o700)
    elif partial in {"wrong-root", "wrong-index"}:
        runner._wrong_root(action).mkdir(mode=0o700)
        if partial == "wrong-index":
            (runner._wrong_root(action) / "index.html").write_bytes(runner._WRONG_INDEX)
    preserved = {
        path: (path.stat().st_ino, path.read_bytes() if path.is_file() else None)
        for root in (attempt, runner._wrong_root(action))
        for path in (root, *root.rglob("*"))
        if path.exists()
    }
    report = runner.run_service_lab(replace(action, operation="inspect"))
    assert report.error == "interrupted-attempt"
    assert not report.started
    assert machine.unit.read_bytes() == machine.original
    assert machine.commands == []
    report = runner.run_service_lab(action)
    assert report.error is None
    assert report.started
    assert not report.healthy
    assert (attempt.parent / "current").read_text(encoding="ascii") == action.run_id
    assert all(
        (path.stat().st_ino, path.read_bytes() if path.is_file() else None) == snapshot
        for path, snapshot in preserved.items()
    )


@pytest.mark.parametrize("scenario", ["missing-executable", "empty-root"])
@pytest.mark.parametrize("phase", [None, "active", "prepared", "aborted"])
def test_persisted_attempts_survive_fault_path_changes(
    machine: _Machine, phase: str | None, scenario: ServiceLabScenario
) -> None:
    """Old durable injections remain inspectable, recoverable, and safe to retry."""
    action = ServiceLabAction(run_id="a" * 32, scenario=scenario, operation="start")
    attempt = machine.home / runner._STATE / action.run_id
    attempt.mkdir(parents=True, mode=0o700)
    attempt.parent.chmod(0o700)
    injected = machine.original.replace(
        b"/usr/bin/caddy", str(attempt / "missing-caddy").encode(), 1
    )
    if scenario == "empty-root":
        injected = machine.original.replace(
            b"%h/public_html", str(attempt / "empty-root").encode(), 1
        )
        (attempt / "empty-root").mkdir(mode=0o700)
        (machine.home / "empty-site").write_bytes(b"unrelated learner file\n")
    (attempt / "original.service").write_bytes(machine.original)
    (attempt / "injected.service").write_bytes(injected)
    if phase is not None:
        (attempt / "attempt").write_text(f"{scenario}\n{phase}\n", encoding="ascii")
    if phase in {"active", "prepared"}:
        machine.unit.write_bytes(injected)
        machine.state.update(loaded=injected.decode(), ActiveState="failed", SubState="failed")
    if phase == "prepared":
        assert runner.run_service_lab(replace(action, operation="inspect")).error == (
            "interrupted-attempt"
        )
        assert machine.unit.read_bytes() == machine.original
    report = runner.run_service_lab(action)
    assert report.error is None
    assert report.started
    assert not report.healthy
    assert machine.unit.read_bytes() == injected
    assert (attempt / "injected.service").read_bytes() == injected
    count = len(machine.commands)
    machine.repair()
    report = runner.run_service_lab(replace(action, operation="inspect"))
    assert report.error is None
    assert report.started
    assert report.healthy
    assert not any("restart" in command for command in machine.commands[count:])
    if scenario == "empty-root":
        assert (machine.home / "empty-site").read_bytes() == b"unrelated learner file\n"


@pytest.mark.parametrize("collision", ["directory", "content", "file", "symlink", "dangling"])
def test_empty_root_never_adopts_existing_learner_paths(machine: _Machine, collision: str) -> None:
    """Existing learner paths must remain untouched across repeated attempts."""
    root = machine.home / "empty-site"
    if collision in {"directory", "content"}:
        root.mkdir(mode=0o700)
        if collision == "content":
            (root / "index.html").write_bytes(b"learner page\n")
    elif collision == "file":
        root.write_bytes(b"learner file\n")
    else:
        root.symlink_to(machine.home / ("public_html" if collision == "symlink" else "missing"))
    metadata = root.lstat()
    action = ServiceLabAction(run_id="a" * 32, scenario="empty-root", operation="start")
    for _attempt in range(2):
        report = runner.run_service_lab(action)
        assert report.error == "unit-changed"
        assert not report.started
        assert root.lstat() == metadata
        assert machine.unit.read_bytes() == machine.original
    if collision == "content":
        assert (root / "index.html").read_bytes() == b"learner page\n"
    elif collision == "file":
        assert root.read_bytes() == b"learner file\n"
    assert not any("restart" in command for command in machine.commands)


@pytest.mark.parametrize("checkpoint", ["before-move", "after-move", "collision"])
def test_empty_root_publication_recovers_without_clobbering(
    machine: _Machine, monkeypatch: pytest.MonkeyPatch, checkpoint: str
) -> None:
    """Interrupted publication must recover without replacing a colliding learner path."""
    action = ServiceLabAction(run_id="a" * 32, scenario="empty-root", operation="start")
    move = runner._move_no_replace

    def interrupt_move(
        source_directory: int, source: str, destination_directory: int, destination: str
    ) -> None:
        if destination == "empty-site":
            if checkpoint == "collision":
                (machine.home / "empty-site").mkdir(mode=0o700)
            elif checkpoint == "before-move":
                raise KeyboardInterrupt
        move(source_directory, source, destination_directory, destination)
        if destination == "empty-site":
            raise KeyboardInterrupt

    with monkeypatch.context() as patch:
        patch.setattr(runner, "_move_no_replace", interrupt_move)
        if checkpoint == "collision":
            assert runner.run_service_lab(action).error == "unit-changed"
        else:
            with pytest.raises(KeyboardInterrupt):
                runner.run_service_lab(action)
    assert machine.unit.read_bytes() == machine.original
    report = runner.run_service_lab(action)
    if checkpoint == "collision":
        assert report.error == "unit-changed"
        assert not report.started
    else:
        assert report.error is None
        assert report.started
        assert report.http_status == 404


def test_initialization_does_not_replace_a_concurrent_artifact(
    machine: _Machine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file created between the missing-file read and publication must win."""
    action = ServiceLabAction(run_id="a" * 32, scenario="missing-executable", operation="start")
    original = machine.home / runner._STATE / action.run_id / "original.service"
    move = runner._move_no_replace

    def create_before_publication(
        source_directory: int, source: str, destination_directory: int, destination: str
    ) -> None:
        if destination == "original.service":
            original.write_bytes(b"concurrent retained edit\n")
        move(source_directory, source, destination_directory, destination)

    monkeypatch.setattr(runner, "_move_no_replace", create_before_publication)
    report = runner.run_service_lab(action)
    assert report.error is not None
    assert not report.started
    assert original.read_bytes() == b"concurrent retained edit\n"
    assert runner.run_service_lab(action).error == "unit-changed"
    assert original.read_bytes() == b"concurrent retained edit\n"
    assert machine.unit.read_bytes() == machine.original
    assert not any("restart" in command for command in machine.commands)


@pytest.mark.parametrize("checkpoint", ["current", "before-phase", "prepared"])
def test_initialization_claims_current_before_directory_and_mutation_phase(
    machine: _Machine, monkeypatch: pytest.MonkeyPatch, checkpoint: str
) -> None:
    """An earlier repaired run cannot leave a stale owner across initialization crashes."""
    action = ServiceLabAction(run_id="a" * 32, scenario="empty-root", operation="start")
    assert runner.run_service_lab(replace(action, run_id="b" * 32)).started
    machine.repair()
    attempt = machine.home / runner._STATE / action.run_id
    write = runner._write
    phase = runner._phase

    def interrupt_current(
        directory: int, name: str, content: bytes, mode: int = 0o600, *, exclusive: bool = False
    ) -> None:
        write(directory, name, content, mode, exclusive=exclusive)
        if name == "current":
            assert not attempt.exists()
            raise KeyboardInterrupt

    def interrupt_phase(directory: int, selected: ServiceLabAction, value: str) -> None:
        assert (attempt.parent / "current").read_text(encoding="ascii") == action.run_id
        if checkpoint == "prepared":
            phase(directory, selected, value)
        raise KeyboardInterrupt

    count = len(machine.commands)
    with monkeypatch.context() as patch:
        if checkpoint == "current":
            patch.setattr(runner, "_write", interrupt_current)
        else:
            patch.setattr(runner, "_phase", interrupt_phase)
        with pytest.raises(KeyboardInterrupt):
            runner.run_service_lab(action)
    assert machine.unit.read_bytes() == machine.original
    assert not any("restart" in command for command in machine.commands[count:])
    assert (attempt.parent / "current").read_text(encoding="ascii") == action.run_id
    if checkpoint == "prepared":
        assert runner.run_service_lab(action).error == "interrupted-attempt"
        assert machine.unit.read_bytes() == machine.original
    assert runner.run_service_lab(action).started


@pytest.mark.parametrize("phase", [None, "prepared", "aborted"])
def test_incomplete_attempt_cannot_reclaim_a_later_active_runs_ownership(
    machine: _Machine, phase: str | None
) -> None:
    """Even a repaired later active run owns current until a genuinely new run starts."""
    action = ServiceLabAction(run_id="a" * 32, scenario="empty-root", operation="start")
    attempt = machine.home / runner._STATE / action.run_id
    attempt.mkdir(parents=True, mode=0o700)
    attempt.parent.chmod(0o700)
    (attempt / "original.service").write_bytes(machine.original)
    if phase is not None:
        (attempt / "injected.service").write_bytes(
            runner._fault(machine.original, action, attempt)[0]
        )
        (attempt / "attempt").write_text(f"empty-root\n{phase}\n", encoding="ascii")
    assert runner.run_service_lab(replace(action, run_id="b" * 32)).started
    machine.repair()
    preserved = {path: path.read_bytes() for path in attempt.iterdir()}
    count = len(machine.commands)
    assert runner.run_service_lab(action).error == "previous-unrecovered"
    assert (attempt.parent / "current").read_text(encoding="ascii") == "b" * 32
    assert {path: path.read_bytes() for path in attempt.iterdir()} == preserved
    assert machine.unit.read_bytes() == machine.original
    assert len(machine.commands) == count


@pytest.mark.parametrize("scenario", SERVICE_LAB_SCENARIOS)
@pytest.mark.parametrize("interrupted", [False, True])
def test_failed_preparation_requires_a_later_explicit_start_retry(  # noqa: PLR0915 - shared rollback and retry lifecycle
    machine: _Machine,
    monkeypatch: pytest.MonkeyPatch,
    interrupted: bool,
    scenario: ServiceLabScenario,
) -> None:
    """Rollback grants no credit; only a later start retries, then active is exactly once."""
    action = ServiceLabAction(run_id="a" * 32, scenario=scenario, operation="start")
    if scenario == "missing-published-site":
        displace = runner._displace_site

        def fail_after_move(home: Path, attempt: int) -> None:
            displace(home, attempt)
            monkeypatch.setattr(runner, "_displace_site", displace)
            if interrupted:
                raise KeyboardInterrupt
            raise ServiceLabError("runner-unavailable")

        monkeypatch.setattr(runner, "_displace_site", fail_after_move)
    else:
        machine.state["interrupt" if interrupted else "fail-reload"] = "yes"
    if interrupted:
        with pytest.raises(KeyboardInterrupt):
            runner.run_service_lab(action)
        assert (machine.unit.read_bytes() == machine.original) == (
            scenario == "missing-published-site"
        )
        report = runner.run_service_lab(replace(action, operation="inspect"))
        assert report.error == "interrupted-attempt"
    else:
        report = runner.run_service_lab(action)
        assert report.error == "injection-failed"
    assert not report.started
    assert not report.healthy
    assert machine.unit.read_bytes() == machine.original
    assert (machine.home / "public_html/index.html").read_bytes() == b"current real homepage\n"
    attempt = machine.home / runner._STATE / action.run_id
    if scenario == "missing-published-site":
        assert not (attempt / "pending-site").exists()
    preserved = {
        path: (path.stat().st_ino, path.read_bytes()) for path in attempt.glob("*.service")
    }
    count = len(machine.commands)
    report = runner.run_service_lab(replace(action, operation="inspect"))
    assert report.error == "injection-failed"
    assert not report.started
    assert not report.healthy
    assert not any("restart" in command for command in machine.commands[count:])
    assert machine.unit.read_bytes() == machine.original
    report = runner.run_service_lab(action)
    assert report.error is None
    assert report.started
    assert not report.healthy
    assert (machine.unit.read_bytes() == machine.original) == (scenario == "missing-published-site")
    assert all(
        (path.stat().st_ino, path.read_bytes()) == snapshot for path, snapshot in preserved.items()
    )
    count = len(machine.commands)
    assert runner.run_service_lab(action).started
    machine.repair()
    if scenario == "missing-published-site":
        machine.rebuild()
    assert runner.run_service_lab(action).healthy
    assert machine.unit.read_bytes() == machine.original
    assert not any("restart" in command for command in machine.commands[count:])
    if scenario == "missing-published-site":
        assert not any(
            operation in command
            for command in machine.commands
            for operation in ("restart", "daemon-reload", "reset-failed")
        )


def test_each_failed_start_stops_after_one_preparation_and_rollback(machine: _Machine) -> None:
    """A transient failure requires another explicit start, never an in-request retry loop."""
    action = ServiceLabAction(run_id="a" * 32, scenario="empty-root", operation="start")
    for _request in range(2):
        machine.state["fail-reload"] = "yes"
        count = len(machine.commands)
        report = runner.run_service_lab(action)
        assert report.error == "injection-failed"
        assert not report.started
        assert not report.healthy
        assert machine.unit.read_bytes() == machine.original
        assert sum("daemon-reload" in command for command in machine.commands[count:]) == 2
    assert runner.run_service_lab(action).started


@pytest.mark.parametrize("replacement", ["rebuilt", "empty", "symlink"])
@pytest.mark.parametrize("interrupted", [False, True])
def test_published_recovery_never_replaces_a_concurrent_rebuild(  # noqa: PLR0915 - shared recovery and retry lifecycle
    machine: _Machine, monkeypatch: pytest.MonkeyPatch, replacement: str, interrupted: bool
) -> None:
    """Even a rebuild at the reverse rename boundary wins; retained backups cannot block retries."""
    action = ServiceLabAction(run_id="a" * 32, scenario="missing-published-site", operation="start")
    root = machine.home / "public_html"
    displace = runner._displace_site
    move = runner._move_no_replace
    replacements: list[int] = []

    def fail_after_move(home: Path, attempt: int) -> None:
        displace(home, attempt)
        monkeypatch.setattr(runner, "_displace_site", displace)
        if interrupted:
            raise KeyboardInterrupt
        raise ServiceLabError("runner-unavailable")

    def rebuild_before_restore(
        source_directory: int, source: str, destination_directory: int, destination: str
    ) -> None:
        if destination == "public_html" and not replacements:
            if replacement == "rebuilt":
                machine.rebuild()
            elif replacement == "empty":
                root.mkdir()
            else:
                root.symlink_to(machine.home / "src/website", target_is_directory=True)
            replacements.append(root.lstat().st_ino)
        move(source_directory, source, destination_directory, destination)

    monkeypatch.setattr(runner, "_displace_site", fail_after_move)
    monkeypatch.setattr(runner, "_move_no_replace", rebuild_before_restore)
    if interrupted:
        with pytest.raises(KeyboardInterrupt):
            runner.run_service_lab(action)
        report = runner.run_service_lab(replace(action, operation="inspect"))
        assert report.error == "interrupted-attempt"
    else:
        report = runner.run_service_lab(action)
        assert report.error == "injection-failed"
    assert not report.started
    assert not report.healthy
    assert replacements == [root.lstat().st_ino]
    if replacement == "symlink":
        assert root.is_symlink()
        root.unlink()
    elif replacement == "empty":
        assert not list(root.iterdir())
    else:
        assert (root / "index.html").read_bytes() == b"rebuilt real homepage\n"
    attempt = machine.home / runner._STATE / action.run_id
    assert not (attempt / "pending-site").exists()
    backup = next(attempt.glob("published-*"))
    assert (backup / "index.html").read_bytes() == b"current real homepage\n"
    assert (backup / "assets/site.css").read_bytes() == b"generated stylesheet\n"
    machine.rebuild()
    assert runner.run_service_lab(action).started
    assert len(list(attempt.glob("published-*"))) == 2
    assert (backup / "index.html").read_bytes() == b"current real homepage\n"
    assert (machine.home / "src/website/source.astro").read_bytes() == b"learner source\n"
    assert machine.unit.read_bytes() == machine.original
    assert not any(
        operation in command
        for command in machine.commands
        for operation in ("restart", "daemon-reload", "reset-failed")
    )


def test_completed_site_recovery_cannot_restore_an_old_backup_during_a_later_publisher_gap(
    machine: _Machine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed retry before new displacement must not resurrect consumed recovery intent."""
    action = ServiceLabAction(run_id="a" * 32, scenario="missing-published-site", operation="start")
    root = machine.home / "public_html"
    previous = machine.home / ".public_html-previous"
    staging = machine.home / ".public_html-staging"
    displace = runner._displace_site

    def fail_after_rebuild(home: Path, attempt: int) -> None:
        displace(home, attempt)
        machine.rebuild()
        raise ServiceLabError("runner-unavailable")

    monkeypatch.setattr(runner, "_displace_site", fail_after_rebuild)
    assert runner.run_service_lab(action).error == "injection-failed"
    attempt = machine.home / runner._STATE / action.run_id
    backup = next(attempt.glob("published-*"))
    assert not (attempt / "pending-site").exists()
    assert (root / "index.html").read_bytes() == b"rebuilt real homepage\n"
    staging.mkdir()
    (staging / "index.html").write_bytes(b"latest publication\n")

    def fail_during_publisher_gap(home: Path, attempt: int) -> None:
        root.rename(previous)
        displace(home, attempt)

    monkeypatch.setattr(runner, "_displace_site", fail_during_publisher_gap)
    assert runner.run_service_lab(action).error == "injection-failed"
    assert not root.exists()
    assert not (attempt / "pending-site").exists()
    assert (backup / "index.html").read_bytes() == b"current real homepage\n"
    assert (previous / "index.html").read_bytes() == b"rebuilt real homepage\n"
    staging.rename(root)
    assert (root / "index.html").read_bytes() == b"latest publication\n"
    assert machine.unit.read_bytes() == machine.original
    assert not any("restart" in command for command in machine.commands)
    monkeypatch.setattr(runner, "_displace_site", displace)
    assert runner.run_service_lab(action).started


@pytest.mark.parametrize("direction", ["displace", "restore"])
def test_native_site_move_denial_retains_recoverable_intent(
    machine: _Machine, direction: str
) -> None:
    """Real renameat2 EACCES leaves data intact and failed restoration retryable."""
    root = machine.home / "public_html"
    attempt = machine.home / runner._STATE / ("a" * 32)
    attempt.mkdir(parents=True, mode=0o700)
    with runner._directory(attempt, private=True) as directory:
        if direction == "restore":
            runner._displace_site(machine.home, directory)
            protected = next(attempt.glob("published-*"))
        else:
            protected = root
        protected.chmod(0o500)
        try:
            with pytest.raises(PermissionError) as failure:
                (runner._restore_site if direction == "restore" else runner._displace_site)(
                    machine.home, directory
                )
            assert failure.value.errno == errno.EACCES
            assert (attempt / "pending-site").exists()
            assert (protected / "index.html").read_bytes() == b"current real homepage\n"
        finally:
            protected.chmod(0o755)
        runner._restore_site(machine.home, directory)
    assert not (attempt / "pending-site").exists()
    assert (root / "index.html").read_bytes() == b"current real homepage\n"


@pytest.mark.parametrize("race", ["interrupted-intent", "directory", "symlink", "cross-device"])
def test_published_preparation_records_identity_and_refuses_raced_sources(
    machine: _Machine, monkeypatch: pytest.MonkeyPatch, race: str
) -> None:
    """Only the recorded inode may be restored, and EXDEV must never become copy/delete."""
    action = ServiceLabAction(run_id="a" * 32, scenario="missing-published-site", operation="start")
    root = machine.home / "public_html"
    original = root.stat()
    attempt = machine.home / runner._STATE / action.run_id
    move = runner._move_no_replace

    def race_before_move(
        source_directory: int, source: str, destination_directory: int, destination: str
    ) -> None:
        if source != "public_html":
            move(source_directory, source, destination_directory, destination)
            return
        assert (attempt / "attempt").read_text(
            encoding="ascii"
        ) == "missing-published-site\nprepared\n"
        assert (attempt / "pending-site").read_text(encoding="ascii").splitlines() == [
            destination.removeprefix("published-"),
            str(original.st_dev),
            str(original.st_ino),
        ]
        monkeypatch.setattr(runner, "_move_no_replace", move)
        if race == "interrupted-intent":
            raise KeyboardInterrupt
        if race == "cross-device":
            raise OSError(errno.EXDEV, "different filesystems")
        root.rename(machine.home / "publisher-previous")
        if race == "directory":
            machine.rebuild()
        else:
            root.symlink_to(machine.home / "src/website", target_is_directory=True)
        move(source_directory, source, destination_directory, destination)

    monkeypatch.setattr(runner, "_move_no_replace", race_before_move)
    if race == "interrupted-intent":
        with pytest.raises(KeyboardInterrupt):
            runner.run_service_lab(action)
        report = runner.run_service_lab(action)
        assert report.error == "interrupted-attempt"
    else:
        report = runner.run_service_lab(action)
        assert report.error == ("injection-failed" if race == "cross-device" else "unit-changed")
    assert not report.started
    assert not report.healthy
    if race in {"interrupted-intent", "cross-device"}:
        assert root.stat().st_ino == original.st_ino
        assert (root / "index.html").read_bytes() == b"current real homepage\n"
        assert not list(attempt.glob("published-*"))
    else:
        assert not root.exists(follow_symlinks=False)
        assert (machine.home / "publisher-previous").stat().st_ino == original.st_ino
        backup = next(attempt.glob("published-*"))
        if race == "directory":
            assert (backup / "index.html").read_bytes() == b"rebuilt real homepage\n"
        else:
            assert backup.is_symlink()
        machine.rebuild()
    assert runner.run_service_lab(action).started
    assert (machine.home / "src/website/source.astro").read_bytes() == b"learner source\n"
    assert machine.unit.read_bytes() == machine.original
    assert not any(
        operation in command
        for command in machine.commands
        for operation in ("restart", "daemon-reload", "reset-failed")
    )


def _no_sleep(_seconds: float) -> None:
    pass


@pytest.mark.parametrize("changed", ["MainPID", "ExecMainStartTimestampMonotonic"])
def test_missing_output_requires_the_original_running_process(
    machine: _Machine, monkeypatch: pytest.MonkeyPatch, changed: str
) -> None:
    """A 404 from a replacement process cannot witness the no-restart scenario."""
    displace = runner._displace_site
    clock = iter(range(1000))
    monkeypatch.setattr(runner.time, "monotonic", lambda: next(clock) / 2)
    monkeypatch.setattr(runner.time, "sleep", _no_sleep)

    def restart_after_move(home: Path, attempt: int) -> None:
        displace(home, attempt)
        machine.state[changed] = "456"

    monkeypatch.setattr(runner, "_displace_site", restart_after_move)
    report = runner.run_service_lab(
        ServiceLabAction(run_id="a" * 32, scenario="missing-published-site", operation="start")
    )
    assert report.error == "injection-failed"
    assert not report.started
    assert not report.healthy
    assert (machine.home / "public_html/index.html").read_bytes() == b"current real homepage\n"
    assert machine.unit.read_bytes() == machine.original


@pytest.mark.parametrize(
    ("scenario", "change"),
    [
        ("missing-executable", "target-file"),
        ("missing-executable", "original-backup"),
        ("missing-executable", "injected-backup"),
        ("empty-root", "empty-root-content"),
        ("empty-root", "empty-root-symlink"),
        ("empty-root", "empty-root-replaced"),
        ("empty-root", "unit-edit"),
        ("empty-root", "unit-mode"),
        ("empty-root", "unhealthy"),
        ("wrong-content", "wrong-root-content"),
        ("wrong-content", "wrong-root-symlink"),
        ("wrong-content", "wrong-index-symlink"),
    ],
)
@pytest.mark.parametrize("preparation", ["initializing", "aborted"])
def test_preparation_retry_refuses_changed_units_and_fault_targets(  # noqa: C901, PLR0912, PLR0915 - refusal matrix
    machine: _Machine,
    monkeypatch: pytest.MonkeyPatch,
    scenario: ServiceLabScenario,
    change: str,
    preparation: str,
) -> None:
    """A technical retry may neither overwrite later edits nor reuse unsafe fault targets."""
    action = ServiceLabAction(run_id="a" * 32, scenario=scenario, operation="start")
    if preparation == "initializing":
        with monkeypatch.context() as patch:

            def interrupt_phase(_directory: int, _action: ServiceLabAction, _phase: str) -> None:
                raise KeyboardInterrupt

            patch.setattr(runner, "_phase", interrupt_phase)
            with pytest.raises(KeyboardInterrupt):
                runner.run_service_lab(action)
    else:
        machine.state["fail-reload"] = "yes"
        assert runner.run_service_lab(action).error == "injection-failed"
    attempt = machine.home / runner._STATE / action.run_id
    if change == "target-file":
        (attempt / "missing-caddy").write_bytes(b"learner-owned file\n")
        lstat = Path.lstat

        def occupied_executable(path: Path) -> os.stat_result:
            return lstat(attempt / "missing-caddy" if path == Path("/usr/bin/cadddyyy") else path)

        monkeypatch.setattr(Path, "lstat", occupied_executable)
    elif change in {"original-backup", "injected-backup"}:
        (attempt / f"{change.removesuffix('-backup')}.service").write_bytes(
            b"retained learner edit\n"
        )
    elif change == "empty-root-content":
        (machine.home / "empty-site/index.html").write_bytes(b"learner-owned page\n")
    elif change in {"empty-root-symlink", "empty-root-replaced"}:
        (machine.home / "empty-site").rename(machine.home / "saved-empty-site")
        if change == "empty-root-replaced":
            (machine.home / "empty-site").mkdir(mode=0o700)
        else:
            (machine.home / "empty-site").symlink_to(
                machine.home / "public_html", target_is_directory=True
            )
    elif change == "wrong-root-content":
        (runner._wrong_root(action) / "index.html").write_bytes(b"learner-owned page\n")
    elif change == "wrong-root-symlink":
        runner._wrong_root(action).rename(machine.home / "saved-wrong-root")
        runner._wrong_root(action).symlink_to(
            machine.home / "public_html", target_is_directory=True
        )
    elif change == "wrong-index-symlink":
        (runner._wrong_root(action) / "index.html").unlink()
        (runner._wrong_root(action) / "index.html").symlink_to(
            machine.home / "public_html/index.html"
        )
    elif change == "unit-edit":
        machine.unit.write_bytes(machine.original + b"# unrelated learner edit\n")
        machine.state["loaded"] = machine.unit.read_text(encoding="utf-8")
    elif change == "unit-mode":
        machine.unit.chmod(0o400)
    else:
        machine.state["bad-http"] = "yes"
    before = machine.unit.read_bytes(), machine.unit.stat().st_mode
    private_paths = {
        path: path.read_bytes() if path.is_file() else None for path in attempt.iterdir()
    }
    count = len(machine.commands)
    report = runner.run_service_lab(action)
    assert report.error is not None
    assert not report.started
    assert not report.healthy
    assert (machine.unit.read_bytes(), machine.unit.stat().st_mode) == before
    assert {
        path: path.read_bytes() if path.is_file() else None for path in attempt.iterdir()
    } == private_paths
    assert not any(
        operation in command
        for command in machine.commands[count:]
        for operation in ("restart", "daemon-reload", "reset-failed")
    )
    if change == "wrong-root-content":
        assert (runner._wrong_root(action) / "index.html").read_bytes() == b"learner-owned page\n"
    elif change == "wrong-root-symlink":
        assert runner._wrong_root(action).is_symlink()
    elif change == "wrong-index-symlink":
        assert (runner._wrong_root(action) / "index.html").is_symlink()


def test_rollback_and_active_inspection_preserve_unrelated_edits(machine: _Machine) -> None:
    """Technical recovery never overwrites a learner's concurrent or later changes."""
    action = ServiceLabAction(run_id="a" * 32, scenario="missing-executable", operation="start")
    machine.state.update({"fail-reload": "yes", "concurrent-edit": "yes"})
    report = runner.run_service_lab(action)
    assert report.error == "rollback-failed"
    assert not report.started
    assert machine.unit.read_text(encoding="utf-8") == "learner's unrelated edit\n"
    assert runner.run_service_lab(action).error == "rollback-failed"
    assert machine.unit.read_text(encoding="utf-8") == "learner's unrelated edit\n"


@pytest.mark.parametrize("scenario", SERVICE_LAB_SCENARIOS)
def test_unwitnessed_fault_cannot_receive_credit(
    machine: _Machine, monkeypatch: pytest.MonkeyPatch, scenario: ServiceLabScenario
) -> None:
    """Writing and restarting successfully cannot substitute for the expected outcome."""
    clock = iter(range(1000))
    monkeypatch.setattr(runner.time, "monotonic", lambda: next(clock) / 2)
    monkeypatch.setattr(runner.time, "sleep", _no_sleep)
    machine.state["unwitnessed"] = "yes"
    report = runner.run_service_lab(
        ServiceLabAction(run_id="a" * 32, scenario=scenario, operation="start")
    )
    assert not report.started
    assert not report.healthy
    assert report.error == "injection-failed"
    assert machine.unit.read_bytes() == machine.original
    assert (machine.home / "public_html/index.html").read_bytes() == b"current real homepage\n"


@pytest.mark.parametrize("mistake", ["wrong-root", "typo", "unknown-field"])
def test_active_student_mistake_has_fresh_diagnostics_without_mutation(
    machine: _Machine, mistake: str
) -> None:
    """A failed repair remains diagnosable without running or rewriting a custom unit."""
    action = ServiceLabAction(run_id="a" * 32, scenario="empty-root", operation="start")
    assert runner.run_service_lab(action).started
    if mistake == "wrong-root":
        machine.unit.write_bytes(machine.original.replace(b"%h/public_html", b"%h/wrong-root"))
    elif mistake == "typo":
        machine.unit.write_bytes(machine.original.replace(b"ExecStart=", b"ExecStrat="))
    else:
        machine.unit.write_bytes(
            machine.original.replace(
                b"Restart=on-failure", b"Restart=on-failure\nUnrecognizedField=yes"
            )
        )
    machine.state["loaded"] = machine.original.decode()
    machine.state["journal"] = "fresh diagnosis after the learner's unsuccessful repair\n"
    before = machine.unit.read_bytes()
    count = len(machine.commands)
    report = runner.run_service_lab(replace(action, operation="inspect"))
    assert report.started
    assert not report.healthy
    assert report.error == "unsafe-unit"
    assert report.unit == before.decode()
    assert "NeedDaemonReload=yes" in report.status
    assert report.journal == machine.state["journal"]
    assert report.http_status == 200
    service_lab_report_payload(report)
    assert machine.unit.read_bytes() == before
    assert not any(
        operation in command
        for command in machine.commands[count:]
        for operation in ("restart", "daemon-reload", "reset-failed")
    )


@pytest.mark.parametrize(
    "partial",
    [
        "prepared-before-write",
        "prepared-without-current",
        "displaced-before-link",
        "linked-before-cleanup",
        "interrupted-recovery",
    ],
)
def test_prepared_attempts_recover_without_injecting_in_that_request(
    machine: _Machine, monkeypatch: pytest.MonkeyPatch, partial: str
) -> None:
    """Recover tentative work without credit; only a later start may retry an aborted attempt."""
    action = ServiceLabAction(run_id="a" * 32, scenario="missing-executable", operation="start")
    attempt = machine.home / runner._STATE / action.run_id
    attempt.mkdir(parents=True, mode=0o700)
    attempt.parent.chmod(0o700)
    (attempt / "original.service").write_bytes(machine.original)
    (attempt / "injected.service").write_bytes(runner._fault(machine.original, action, attempt)[0])
    (attempt / "attempt").write_text("missing-executable\nprepared\n", encoding="ascii")
    if partial != "prepared-without-current":
        (attempt.parent / "current").write_text(action.run_id, encoding="ascii")
    if partial in {"displaced-before-link", "linked-before-cleanup", "interrupted-recovery"}:
        (attempt / "pending-unit").write_text("c" * 32, encoding="ascii")
        (attempt / f"candidate-{'c' * 32}.service").write_bytes(
            (attempt / "injected.service").read_bytes()
        )
        machine.unit.rename(attempt / f"displaced-{'c' * 32}.service")
        if partial == "linked-before-cleanup":
            machine.unit.hardlink_to(attempt / f"candidate-{'c' * 32}.service")
    if partial == "interrupted-recovery":
        unlink = runner.os.unlink
        interrupted: list[str] = []

        def interrupt_cleanup(name: str, *, dir_fd: int) -> None:
            if name.startswith("recovered-") and not interrupted:
                interrupted.append(name)
                raise KeyboardInterrupt
            unlink(name, dir_fd=dir_fd)

        monkeypatch.setattr(runner.os, "unlink", interrupt_cleanup)
        with pytest.raises(KeyboardInterrupt):
            runner.run_service_lab(action)
        assert interrupted == [f"recovered-{'c' * 32}.service"]
        assert machine.unit.stat().st_nlink == 2
        assert (attempt / "pending-unit").exists()
    report = runner.run_service_lab(action)
    assert report.error == "interrupted-attempt"
    assert not report.started
    assert not report.healthy
    assert machine.unit.read_bytes() == machine.original
    assert machine.unit.stat().st_nlink == 1
    count = len(machine.commands)
    assert not runner.run_service_lab(replace(action, operation="inspect")).started
    assert machine.unit.read_bytes() == machine.original
    assert not any("restart" in command for command in machine.commands[count:])
    if partial in {"displaced-before-link", "linked-before-cleanup", "interrupted-recovery"}:
        assert (attempt / f"displaced-{'c' * 32}.service").read_bytes() == machine.original
        assert not (attempt / "pending-unit").exists()
    if partial == "interrupted-recovery":
        assert not (attempt / f"recovered-{'c' * 32}.service").exists()
    assert runner.run_service_lab(action).started


@pytest.mark.parametrize("phase", ["injection", "rollback"])
@pytest.mark.parametrize(
    "race", ["before-displacement", "before-publication", "after-displacement-check"]
)
def test_publication_preserves_edits_racing_with_injection_and_rollback(  # noqa: C901 - paired publication race matrix
    machine: _Machine, monkeypatch: pytest.MonkeyPatch, phase: str, race: str
) -> None:
    """An editor's new inode or write to the displaced inode must never be silently lost."""
    action = ServiceLabAction(run_id="a" * 32, scenario="missing-executable", operation="start")
    attempt = machine.home / runner._STATE / action.run_id
    edited = machine.original + b"# concurrent editor save after the original backup\n"
    rename = runner.os.rename
    link = runner.os.link
    publications: list[Path] = []
    triggered: list[str] = []
    target_publication = 1 if phase == "injection" else 2
    if phase == "rollback":
        machine.state["fail-reload"] = "yes"

    def editor_save() -> None:
        saved = machine.home / "editor-save"
        saved.write_bytes(edited)
        saved.replace(machine.unit)
        triggered.append(race)

    def displace(
        source: str,
        destination: str,
        *,
        src_dir_fd: int,
        dst_dir_fd: int,
    ) -> None:
        assert source == "site.service"
        publications.append(attempt / destination)
        if len(publications) == target_publication and race == "before-displacement":
            editor_save()
        rename(source, destination, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd)

    def publish(
        source: str,
        destination: str,
        *,
        src_dir_fd: int,
        dst_dir_fd: int,
        follow_symlinks: bool,
    ) -> None:
        if source.startswith("candidate-") and len(publications) == target_publication:
            if race == "before-publication":
                editor_save()
            elif race == "after-displacement-check":
                publications[-1].write_bytes(edited)
                triggered.append(race)
        link(
            source,
            destination,
            src_dir_fd=src_dir_fd,
            dst_dir_fd=dst_dir_fd,
            follow_symlinks=follow_symlinks,
        )

    monkeypatch.setattr(runner.os, "rename", displace)
    monkeypatch.setattr(runner.os, "link", publish)
    report = runner.run_service_lab(action)
    assert triggered == [race]
    assert not report.started
    assert not report.healthy
    assert report.error in {"unit-changed", "rollback-failed"}
    assert (attempt / "original.service").read_bytes() == machine.original
    if race == "before-publication":
        assert machine.unit.read_bytes() == edited
    else:
        assert any(displaced.read_bytes() == edited for displaced in publications)
    assert all(displaced.exists() for displaced in publications)
    if phase != "injection" or race != "after-displacement-check":
        assert not any("restart" in command for command in machine.commands)


def test_editor_descriptor_still_has_a_retained_inode_after_publication(machine: _Machine) -> None:
    """An editor holding the old inode can save after publication without losing its bytes."""
    action = ServiceLabAction(run_id="a" * 32, scenario="empty-root", operation="start")
    edited = machine.original + b"# saved through an already-open editor descriptor\n"
    with machine.unit.open("r+b") as editor:
        assert runner.run_service_lab(action).started
        editor.write(edited)
        editor.truncate()
        editor.flush()
        retained = [
            displaced
            for displaced in (machine.home / runner._STATE / action.run_id).glob("displaced-*")
            if displaced.stat().st_ino == os.fstat(editor.fileno()).st_ino
        ]
        assert len(retained) == 1
        assert retained[0].read_bytes() == edited
    assert machine.unit.read_bytes() != edited


def test_new_run_variant_mismatch_and_busy_lock_cannot_mutate(machine: _Machine) -> None:
    """Unrecovered attempts and concurrent callers cannot stack faults."""
    action = ServiceLabAction(run_id="a" * 32, scenario="empty-root", operation="start")
    assert runner.run_service_lab(action).started
    before = machine.unit.read_bytes()
    count = len(machine.commands)
    assert runner.run_service_lab(replace(action, run_id="b" * 32)).error is not None
    assert (
        runner.run_service_lab(replace(action, scenario="missing-executable")).error
        == "attempt-mismatch"
    )
    with (machine.home / runner._STATE / "lock").open("rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert runner.run_service_lab(action).error == "attempt-busy"
    assert machine.unit.read_bytes() == before
    assert not any("restart" in command for command in machine.commands[count:])


@pytest.mark.parametrize("mismatch", [None, "executable", "cwd", "argv"])
def test_running_process_checks_the_actual_executable_directory_and_arguments(
    temporary_path: Path, monkeypatch: pytest.MonkeyPatch, mismatch: str | None
) -> None:
    """Check real process identity logic using temporary files, without launching a process."""
    executable = temporary_path / "caddy"
    executable.touch(mode=0o755)
    other = temporary_path / "other"
    other.mkdir()
    process = temporary_path / "proc/123"
    process.mkdir(parents=True)
    (process / "exe").symlink_to(other if mismatch == "executable" else executable)
    (process / "cwd").symlink_to(other if mismatch == "cwd" else temporary_path)
    source = b"""[Unit]
Description=Personal website service
[Service]
WorkingDirectory=%h
ExecStart=/usr/bin/caddy file-server --listen :14242 --root %h/public_html --access-log
Restart=on-failure
[Install]
WantedBy=default.target
"""
    arguments = [
        "/usr/bin/caddy",
        "file-server",
        "--listen",
        ":14242",
        "--root",
        f"{temporary_path}/public_html",
        "--access-log",
    ]
    if mismatch == "argv":
        arguments.append("--browse")
    (process / "cmdline").write_bytes(
        b"\0".join(argument.encode() for argument in arguments) + b"\0"
    )
    lstat = Path.lstat

    def bound_path(value: str) -> Path:
        return {"/proc": process.parent, "/usr/bin/caddy": executable}.get(value, Path(value))

    def executable_metadata(path: Path) -> os.stat_result:
        if path == executable:
            return os.stat_result((stat.S_IFREG | 0o755, 0, 0, 1, 0, 0, 0, 0, 0, 0))
        return lstat(path)

    monkeypatch.setattr(runner, "Path", bound_path)
    monkeypatch.setattr(Path, "lstat", executable_metadata)
    if mismatch is None:
        runner._running_process(source, temporary_path, {"MainPID": "123"})
    else:
        with pytest.raises(ServiceLabError, match="unsafe-unit"):
            runner._running_process(source, temporary_path, {"MainPID": "123"})


@pytest.mark.parametrize("identity", ["root", "effective-root", "bot"])
def test_unsafe_identity_refused_before_subprocess(
    monkeypatch: pytest.MonkeyPatch, identity: str
) -> None:
    """Never use a daemon or privileged identity to address a learner's user bus."""
    monkeypatch.setattr(runner.os, "getuid", lambda: 0 if identity == "root" else 4242)
    monkeypatch.setattr(runner.os, "geteuid", lambda: 0 if identity != "bot" else 4242)

    def bot_account(_user_id: int) -> pwd.struct_passwd:
        return pwd.struct_passwd(
            ("maker-guide", "x", 4242, 4242, "", "/var/lib/maker-guide", "/bin/bash")
        )

    monkeypatch.setattr(runner.pwd, "getpwuid", bot_account)

    def unexpected(*_arguments: object, **_keywords: object) -> None:
        raise AssertionError("Unsafe identity reached a subprocess")

    monkeypatch.setattr(runner.subprocess, "Popen", unexpected)
    assert (
        runner.run_service_lab(
            ServiceLabAction(run_id="a" * 32, scenario="empty-root", operation="start")
        ).error
        == "unsafe-user"
    )
