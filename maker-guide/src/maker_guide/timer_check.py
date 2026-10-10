"""Strict contract for the fixed, read-only S9 user-timer probe."""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from typing import cast

from maker_guide.validation_paths import (
    UnixAccountLookup,
    lookup_unix_account,
    open_validation_file,
)

TIMER_CHECK_VERSION = 1
TIMER_CHECK_TIMEOUT_SECONDS = 8.0
TIMER_CHECK_MAX_FRAME_BYTES = 2048
_UNIT_PATHS = (
    "~/.config/systemd/user/site-build.service",
    "~/.config/systemd/user/site-build.timer",
)
_HASH = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True, kw_only=True, slots=True)
class TimerCheckReport:
    """Bounded status values only; never carries command output or unit contents."""

    service_sha256: str
    timer_sha256: str
    timer_loaded: bool
    timer_enabled: bool
    timer_active: bool
    timer_substate: str
    timer_unit: str
    timer_no_reload: bool
    service_loaded: bool
    service_active: bool
    service_no_reload: bool
    next_elapse_us: int
    observed_realtime_us: int
    error: str | None = None


class TimerCheckError(ValueError):
    """Safe timer-check failure token."""

    def __init__(self, reason: str = "invalid-report") -> None:
        allowed = {
            "runner-unavailable",
            "timeout",
            "unsafe-user",
            "unit-unreadable",
            "unit-changed",
            "invalid-report",
        }
        super().__init__(reason if reason in allowed else "invalid-report")


def read_timer_sources(
    handle: str, *, account_lookup: UnixAccountLookup = lookup_unix_account
) -> tuple[bytes, bytes]:
    """Read fixed regular unit files with a strict size bound."""
    sources: list[bytes] = []
    for path in _UNIT_PATHS:
        opened = open_validation_file(handle, path, account_lookup=account_lookup)
        if opened.failure_reason is not None or opened.file_descriptor is None:
            raise TimerCheckError("unit-unreadable")
        try:
            with os.fdopen(opened.file_descriptor, "rb") as file_handle:
                contents = file_handle.read(1024 * 1024 + 1)
            if len(contents) > 1024 * 1024:
                raise TimerCheckError("unit-unreadable")
            contents.decode("utf-8")
        except (OSError, UnicodeError):
            raise TimerCheckError("unit-unreadable") from None
        sources.append(contents)
    return sources[0], sources[1]


def source_digests(service: bytes, timer: bytes) -> tuple[str, str]:
    """Return SHA-256 digests for the two fixed unit sources."""
    return hashlib.sha256(service).hexdigest(), hashlib.sha256(timer).hexdigest()


def timer_check_report_payload(report: TimerCheckReport) -> dict[str, object]:
    """Serialize only the versioned bounded report fields."""
    return {
        "version": TIMER_CHECK_VERSION,
        "service_sha256": report.service_sha256,
        "timer_sha256": report.timer_sha256,
        "timer_loaded": report.timer_loaded,
        "timer_enabled": report.timer_enabled,
        "timer_active": report.timer_active,
        "timer_substate": report.timer_substate,
        "timer_unit": report.timer_unit,
        "timer_no_reload": report.timer_no_reload,
        "service_loaded": report.service_loaded,
        "service_active": report.service_active,
        "service_no_reload": report.service_no_reload,
        "next_elapse_us": report.next_elapse_us,
        "observed_realtime_us": report.observed_realtime_us,
        "error": report.error,
    }


def parse_timer_check_report(
    value: object, service_sha256: str, timer_sha256: str
) -> TimerCheckReport:
    """Validate the exact report schema and bind it to both unit hashes."""
    if (
        not _HASH.fullmatch(service_sha256)
        or not _HASH.fullmatch(timer_sha256)
        or not isinstance(value, dict)
    ):
        raise TimerCheckError
    payload = cast("dict[object, object]", value)
    expected = {
        "version",
        "service_sha256",
        "timer_sha256",
        "timer_loaded",
        "timer_enabled",
        "timer_active",
        "timer_substate",
        "timer_unit",
        "timer_no_reload",
        "service_loaded",
        "service_active",
        "service_no_reload",
        "next_elapse_us",
        "observed_realtime_us",
        "error",
    }
    if (
        set(payload) != expected
        or type(payload["version"]) is not int
        or payload["version"] != TIMER_CHECK_VERSION
    ):
        raise TimerCheckError
    if payload["service_sha256"] != service_sha256 or payload["timer_sha256"] != timer_sha256:
        raise TimerCheckError("unit-changed")
    boolean_fields = (
        "timer_loaded",
        "timer_enabled",
        "timer_active",
        "timer_no_reload",
        "service_loaded",
        "service_active",
        "service_no_reload",
    )
    if any(type(payload[field]) is not bool for field in boolean_fields):
        raise TimerCheckError
    substate = payload["timer_substate"]
    if not isinstance(substate, str) or substate not in {
        "waiting",
        "dead",
        "failed",
        "running",
    }:
        raise TimerCheckError
    unit = payload["timer_unit"]
    if not isinstance(unit, str) or unit not in {"site-build.service", ""}:
        raise TimerCheckError
    for field in ("next_elapse_us", "observed_realtime_us"):
        if (
            type(payload[field]) is not int
            or not 0 <= cast("int", payload[field]) <= 18_446_744_073_709_551_615
        ):
            raise TimerCheckError
    error = payload["error"]
    if error is not None and (
        not isinstance(error, str)
        or error
        not in {
            "runner-unavailable",
            "timeout",
            "unsafe-user",
            "unit-unreadable",
            "unit-changed",
            "invalid-report",
        }
    ):
        raise TimerCheckError
    return TimerCheckReport(
        service_sha256=service_sha256,
        timer_sha256=timer_sha256,
        timer_loaded=cast("bool", payload["timer_loaded"]),
        timer_enabled=cast("bool", payload["timer_enabled"]),
        timer_active=cast("bool", payload["timer_active"]),
        timer_substate=substate,
        timer_unit=unit,
        timer_no_reload=cast("bool", payload["timer_no_reload"]),
        service_loaded=cast("bool", payload["service_loaded"]),
        service_active=cast("bool", payload["service_active"]),
        service_no_reload=cast("bool", payload["service_no_reload"]),
        next_elapse_us=cast("int", payload["next_elapse_us"]),
        observed_realtime_us=cast("int", payload["observed_realtime_us"]),
        error=error,
    )
