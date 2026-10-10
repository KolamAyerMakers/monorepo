"""Protect the fixed read-only S9 timer probe and its bounded report."""

from __future__ import annotations

import os
import pwd

import pytest

from maker_guide.cli import timer_check as local_probe
from maker_guide.timer_check import (
    TimerCheckError,
    TimerCheckReport,
    parse_timer_check_report,
    source_digests,
    timer_check_report_payload,
)

_SERVICE, _TIMER = source_digests(b"service", b"timer")


def _run(
    monkeypatch: pytest.MonkeyPatch, timer_properties: str
) -> tuple[TimerCheckReport, list[list[str]]]:
    account = pwd.struct_passwd(("learner", "x", 1001, 1001, "", "/home/learner", "/bin/bash"))
    monkeypatch.setattr(local_probe.os, "getuid", lambda: 1001)
    monkeypatch.setattr(local_probe.os, "geteuid", lambda: 1001)

    def account_for_uid(_uid: int) -> pwd.struct_passwd:
        return account

    def read_sources(_handle: str) -> tuple[bytes, bytes]:
        return b"service", b"timer"

    monkeypatch.setattr(local_probe.pwd, "getpwuid", account_for_uid)
    monkeypatch.setattr(local_probe, "read_timer_sources", read_sources)
    calls: list[list[str]] = []

    class FakeProcess:
        def __init__(self, arguments: list[str], standard_output: str) -> None:
            del arguments
            stdout_read, stdout_write = os.pipe()
            stderr_read, stderr_write = os.pipe()
            os.write(stdout_write, standard_output.encode())
            os.close(stdout_write)
            os.close(stderr_write)
            self.stdout = os.fdopen(stdout_read, "rb")
            self.stderr = os.fdopen(stderr_read, "rb")

        def poll(self) -> int:
            return 0

        def wait(self, timeout: float | None = None) -> int:
            del timeout
            return 0

        def kill(self) -> None:
            return

    def popen(arguments: list[str], **options: object) -> FakeProcess:
        calls.append(arguments)
        assert options["env"] == {
            "HOME": "/home/learner",
            "USER": "learner",
            "LOGNAME": "learner",
            "XDG_RUNTIME_DIR": "/run/user/1001",
            "PATH": "/usr/bin:/bin",
            "LANG": "C",
            "LC_ALL": "C",
        }
        if arguments[1:3] == ["--user", "show"]:
            output = (
                timer_properties
                if arguments[3] == "site-build.timer"
                else "LoadState=loaded\nActiveState=inactive\nNeedDaemonReload=no\n"
            )
        else:
            output = "t 4102444800000000\n"
        return FakeProcess(arguments, output)

    monkeypatch.setattr(local_probe.subprocess, "Popen", popen)
    return local_probe.run_timer_check(_SERVICE, _TIMER), calls


@pytest.mark.parametrize(
    ("changes", "passes"),
    [
        ({}, True),
        ({"UnitFileState": "disabled"}, False),
        ({"ActiveState": "inactive", "SubState": "dead"}, False),
        ({"NeedDaemonReload": "yes"}, False),
        ({"Unit": "other.service"}, None),
    ],
)
def test_probe_reads_only_fixed_units_and_fails_closed_on_bad_state(
    monkeypatch: pytest.MonkeyPatch, changes: dict[str, str], passes: bool | None
) -> None:
    """Only fixed read-only queries run and unexpected state never counts as success."""
    properties = {
        "LoadState": "loaded",
        "UnitFileState": "enabled",
        "ActiveState": "active",
        "SubState": "waiting",
        "Unit": "site-build.service",
        "NeedDaemonReload": "no",
    } | changes
    text = "".join(f"{key}={value}\n" for key, value in properties.items())
    report, calls = _run(monkeypatch, text)
    if passes is None:
        with pytest.raises(TimerCheckError, match="invalid-report"):
            parse_timer_check_report(timer_check_report_payload(report), _SERVICE, _TIMER)
    else:
        accepted = parse_timer_check_report(timer_check_report_payload(report), _SERVICE, _TIMER)
        assert (
            accepted.timer_enabled and accepted.timer_active and accepted.timer_no_reload
        ) is passes
    assert len(calls) == 3
    assert all(call[0] in {"/usr/bin/systemctl", "/usr/bin/busctl"} for call in calls)
    assert all(call[2] in {"show", "get-property"} for call in calls)


def test_report_rejects_stale_hashes_and_non_boolean_status() -> None:
    """The wire parser rejects hash mismatches and non-boolean state fields."""
    report = TimerCheckReport(
        service_sha256=_SERVICE,
        timer_sha256=_TIMER,
        timer_loaded=True,
        timer_enabled=True,
        timer_active=True,
        timer_substate="waiting",
        timer_unit="site-build.service",
        timer_no_reload=True,
        service_loaded=True,
        service_active=False,
        service_no_reload=True,
        next_elapse_us=100,
        observed_realtime_us=50,
    )
    with pytest.raises(TimerCheckError, match="unit-changed"):
        parse_timer_check_report(timer_check_report_payload(report), "0" * 64, _TIMER)
    payload = timer_check_report_payload(report) | {"timer_active": 1}
    with pytest.raises(TimerCheckError, match="invalid-report"):
        parse_timer_check_report(payload, _SERVICE, _TIMER)
    with pytest.raises(TimerCheckError, match="invalid-report"):
        parse_timer_check_report(
            timer_check_report_payload(report) | {"error": object()}, _SERVICE, _TIMER
        )
