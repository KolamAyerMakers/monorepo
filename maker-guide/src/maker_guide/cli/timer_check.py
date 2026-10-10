"""Probe only the fixed S9 user units, as the authenticated learner."""

from __future__ import annotations

import os
import pwd
import re
import selectors
import subprocess
import time
from contextlib import suppress
from typing import cast

from maker_guide.timer_check import (
    TIMER_CHECK_TIMEOUT_SECONDS,
    TimerCheckError,
    TimerCheckReport,
    read_timer_sources,
    source_digests,
)

_PROPERTIES = (
    "LoadState",
    "UnitFileState",
    "ActiveState",
    "SubState",
    "Unit",
    "NeedDaemonReload",
)
_MAX_OUTPUT = 4096


def _run(arguments: list[str], environment: dict[str, str], deadline: float) -> str:
    process: subprocess.Popen[bytes] | None = None
    try:
        process = subprocess.Popen(  # noqa: S603 - argv is fixed to read-only systemd queries.
            arguments,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
        )
        stdout, stderr = _read_process_output(process, deadline)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimerCheckError("timeout")
        status = process.wait(timeout=remaining)
        if status != 0 or stderr:
            raise TimerCheckError("runner-unavailable")
        return stdout.decode("utf-8", errors="strict")
    except subprocess.TimeoutExpired:
        raise TimerCheckError("timeout") from None
    except (OSError, UnicodeError):
        raise TimerCheckError("runner-unavailable") from None
    finally:
        if process is not None:
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()
            if process.poll() is None:
                process.kill()
                with suppress(subprocess.TimeoutExpired):
                    process.wait(timeout=0.5)


def _read_process_output(process: subprocess.Popen[bytes], deadline: float) -> tuple[bytes, bytes]:
    if process.stdout is None or process.stderr is None:
        raise TimerCheckError("runner-unavailable")
    output = {"stdout": bytearray(), "stderr": bytearray()}
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimerCheckError("timeout")
            for key, _events in selector.select(min(remaining, 0.1)):
                chunk = os.read(key.fd, _MAX_OUTPUT + 1)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                output[cast("str", key.data)].extend(chunk)
                if sum(map(len, output.values())) > _MAX_OUTPUT:
                    raise TimerCheckError("runner-unavailable")
    return bytes(output["stdout"]), bytes(output["stderr"])


def _properties(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        key, separator, value = line.partition("=")
        if not separator or key in values:
            raise TimerCheckError("invalid-report")
        values[key] = value
    return values


def run_timer_check(expected_service_sha256: str, expected_timer_sha256: str) -> TimerCheckReport:
    """Read systemd user-manager state and timer deadline; execute no units."""
    real_uid = os.getuid()
    if real_uid == 0 or os.geteuid() != real_uid:
        raise TimerCheckError("unsafe-user")
    try:
        account = pwd.getpwuid(real_uid)
    except KeyError:
        raise TimerCheckError("unsafe-user") from None
    try:
        service, timer = read_timer_sources(account.pw_name)
    except TimerCheckError:
        raise TimerCheckError("unit-unreadable") from None
    service_sha256, timer_sha256 = source_digests(service, timer)
    if (service_sha256, timer_sha256) != (expected_service_sha256, expected_timer_sha256):
        raise TimerCheckError("unit-changed")
    environment = {
        "HOME": account.pw_dir,
        "USER": account.pw_name,
        "LOGNAME": account.pw_name,
        "XDG_RUNTIME_DIR": f"/run/user/{account.pw_uid}",
        "PATH": "/usr/bin:/bin",
        "LANG": "C",
        "LC_ALL": "C",
    }
    deadline = time.monotonic() + TIMER_CHECK_TIMEOUT_SECONDS
    unit = "site-build.timer"
    timer_values = _properties(
        _run(
            [
                "/usr/bin/systemctl",
                "--user",
                "show",
                unit,
                *(argument for prop in _PROPERTIES for argument in ("-p", prop)),
            ],
            environment,
            deadline,
        )
    )
    service_values = _properties(
        _run(
            [
                "/usr/bin/systemctl",
                "--user",
                "show",
                "site-build.service",
                "-p",
                "LoadState",
                "-p",
                "ActiveState",
                "-p",
                "NeedDaemonReload",
            ],
            environment,
            deadline,
        )
    )
    deadline_text = _run(
        [
            "/usr/bin/busctl",
            "--user",
            "get-property",
            "org.freedesktop.systemd1",
            "/org/freedesktop/systemd1/unit/site_2dbuild_2etimer",
            "org.freedesktop.systemd1.Timer",
            "NextElapseUSecRealtime",
        ],
        environment,
        deadline,
    ).strip()
    match = re.fullmatch(r"t ([0-9]+)", deadline_text)
    if match is None:
        raise TimerCheckError("runner-unavailable")
    required_timer = {
        "LoadState",
        "UnitFileState",
        "ActiveState",
        "SubState",
        "Unit",
        "NeedDaemonReload",
    }
    if set(timer_values) != required_timer or set(service_values) != {
        "LoadState",
        "ActiveState",
        "NeedDaemonReload",
    }:
        raise TimerCheckError("invalid-report")
    now = time.time_ns() // 1000
    return TimerCheckReport(
        service_sha256=service_sha256,
        timer_sha256=timer_sha256,
        timer_loaded=timer_values["LoadState"] == "loaded",
        timer_enabled=timer_values["UnitFileState"] == "enabled",
        timer_active=timer_values["ActiveState"] == "active",
        timer_substate=timer_values["SubState"],
        timer_unit=timer_values["Unit"],
        timer_no_reload=timer_values["NeedDaemonReload"] == "no",
        service_loaded=service_values["LoadState"] == "loaded",
        service_active=service_values["ActiveState"] == "active",
        service_no_reload=service_values["NeedDaemonReload"] == "no",
        next_elapse_us=int(match[1]),
        observed_realtime_us=now,
    )
