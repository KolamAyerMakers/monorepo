"""Bounded S8 action/report contract; transports must reject duplicate JSON keys."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Literal, cast

SERVICE_LAB_VERSION = 1
SERVICE_LAB_TIMEOUT_SECONDS = 25.0
SERVICE_LAB_MAX_FRAME_BYTES = 16384
type ServiceLabScenario = Literal[
    "missing-executable",
    "invalid-argument",
    "empty-root",
    "wrong-content",
    "missing-published-site",
]
SERVICE_LAB_SCENARIOS: tuple[ServiceLabScenario, ...] = (
    "missing-executable",
    "invalid-argument",
    "empty-root",
    "wrong-content",
    "missing-published-site",
)
_ERRORS = frozenset(
    {
        "invalid-action",
        "invalid-report",
        "unsafe-user",
        "unsafe-path",
        "unsafe-unit",
        "baseline-unhealthy",
        "attempt-busy",
        "attempt-mismatch",
        "attempt-missing",
        "previous-unrecovered",
        "interrupted-attempt",
        "injection-failed",
        "rollback-failed",
        "unit-changed",
        "runner-unavailable",
        "timeout",
        "output-limit",
    }
)


@dataclass(frozen=True, kw_only=True, slots=True)
class ServiceLabAction:
    """A daemon-selected attempt, never a caller-selected filesystem path."""

    run_id: str
    scenario: ServiceLabScenario
    operation: Literal["start", "inspect"]


@dataclass(frozen=True, kw_only=True, slots=True)
class ServiceLabReport:
    """Witnessed injection and fresh health, not an asserted completion flag."""

    run_id: str
    scenario: ServiceLabScenario
    started: bool
    healthy: bool
    unit: str = ""
    status: str = ""
    journal: str = ""
    http_status: int | None = None
    error: str | None = None


class ServiceLabError(ValueError):
    """A fixed diagnostic token, never rejected input or exception details."""

    def __init__(self, reason: str = "invalid-report") -> None:
        super().__init__(reason if reason in _ERRORS else "invalid-report")


def parse_service_lab_action(value: object) -> ServiceLabAction:
    """Validate the complete versioned action schema."""
    if not isinstance(value, dict):
        raise ServiceLabError("invalid-action")
    payload = cast("dict[object, object]", value)
    if set(payload) != {"version", "run_id", "scenario", "operation"}:
        raise ServiceLabError("invalid-action")
    if type(payload["version"]) is not int or payload["version"] != SERVICE_LAB_VERSION:
        raise ServiceLabError("invalid-action")
    run_id, scenario, operation = payload["run_id"], payload["scenario"], payload["operation"]
    if (
        not isinstance(run_id, str)
        or re.fullmatch(r"[0-9a-f]{32}", run_id) is None
        or not isinstance(scenario, str)
        or scenario not in SERVICE_LAB_SCENARIOS
        or not isinstance(operation, str)
        or operation not in {"start", "inspect"}
    ):
        raise ServiceLabError("invalid-action")
    return ServiceLabAction(
        run_id=run_id,
        scenario=scenario,
        operation=cast("Literal['start', 'inspect']", operation),
    )


def service_lab_action_payload(action: ServiceLabAction) -> dict[str, object]:
    """Serialize and validate an action before transport."""
    payload = {"version": SERVICE_LAB_VERSION, **cast("dict[str, object]", asdict(action))}
    parse_service_lab_action(payload)
    return payload


def parse_service_lab_report(value: object, expected_action: ServiceLabAction) -> ServiceLabReport:
    """Bind bounded evidence to the expected run and scenario, rejecting contradictions."""
    service_lab_action_payload(expected_action)
    if not isinstance(value, dict):
        raise ServiceLabError("invalid-report")
    payload = cast("dict[object, object]", value)
    if set(payload) != {
        "version",
        "run_id",
        "scenario",
        "started",
        "healthy",
        "unit",
        "status",
        "journal",
        "http_status",
        "error",
    }:
        raise ServiceLabError("invalid-report")
    if (
        type(payload["version"]) is not int
        or payload["version"] != SERVICE_LAB_VERSION
        or payload["run_id"] != expected_action.run_id
        or payload["scenario"] != expected_action.scenario
        or type(payload["started"]) is not bool
        or type(payload["healthy"]) is not bool
    ):
        raise ServiceLabError("invalid-report")
    for name in ("unit", "status", "journal"):
        text = payload[name]
        if (
            not isinstance(text, str)
            or len(text) > 2048
            or any(ord(character) < 32 and character not in "\n\t" for character in text)
            or any(0x7F <= ord(character) <= 0x9F for character in text)
        ):
            raise ServiceLabError("invalid-report")
    http_status, error = payload["http_status"], payload["error"]
    if http_status is not None and (type(http_status) is not int or not 100 <= http_status <= 599):
        raise ServiceLabError("invalid-report")
    if error is not None and (not isinstance(error, str) or error not in _ERRORS):
        raise ServiceLabError("invalid-report")
    if payload["healthy"] and (error is not None or http_status != 200):
        raise ServiceLabError("invalid-report")
    if len(json.dumps(payload, ensure_ascii=True)) > SERVICE_LAB_MAX_FRAME_BYTES:
        raise ServiceLabError("invalid-report")
    return ServiceLabReport(
        run_id=expected_action.run_id,
        scenario=expected_action.scenario,
        started=payload["started"],
        healthy=payload["healthy"],
        unit=cast("str", payload["unit"]),
        status=cast("str", payload["status"]),
        journal=cast("str", payload["journal"]),
        http_status=http_status,
        error=error,
    )


def service_lab_report_payload(report: ServiceLabReport) -> dict[str, object]:
    """Serialize only fixed fields, validating the same boundary as the receiver."""
    payload = {"version": SERVICE_LAB_VERSION, **cast("dict[str, object]", asdict(report))}
    parse_service_lab_report(
        payload,
        ServiceLabAction(run_id=report.run_id, scenario=report.scenario, operation="inspect"),
    )
    return payload
