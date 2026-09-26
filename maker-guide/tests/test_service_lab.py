"""Reject untrusted S8 protocol fields, mismatched attempts and oversized evidence."""

from __future__ import annotations

from dataclasses import replace

import pytest

from maker_guide.service_lab import (
    SERVICE_LAB_SCENARIOS,
    ServiceLabAction,
    ServiceLabError,
    ServiceLabReport,
    ServiceLabScenario,
    parse_service_lab_action,
    parse_service_lab_report,
    service_lab_action_payload,
    service_lab_report_payload,
)

_ACTION = ServiceLabAction(run_id="a" * 32, scenario="empty-root", operation="start")


@pytest.mark.parametrize("scenario", SERVICE_LAB_SCENARIOS)
def test_action_and_report_bind_attempt_and_scenario(scenario: ServiceLabScenario) -> None:
    """Evidence round-trips for every variant, but cannot certify another attempt."""
    action = replace(_ACTION, scenario=scenario)
    assert parse_service_lab_action(service_lab_action_payload(action)) == action
    report = ServiceLabReport(
        run_id=action.run_id, scenario=scenario, started=True, healthy=True, http_status=200
    )
    assert parse_service_lab_report(service_lab_report_payload(report), action) == report
    with pytest.raises(ServiceLabError, match="invalid-report"):
        parse_service_lab_report(
            service_lab_report_payload(report), replace(action, run_id="b" * 32)
        )
    with pytest.raises(ServiceLabError, match="invalid-report"):
        parse_service_lab_report(
            service_lab_report_payload(report),
            replace(
                action, scenario="missing-executable" if scenario == "empty-root" else "empty-root"
            ),
        )


@pytest.mark.parametrize(
    "replacement",
    [
        {"version": True},
        {"version": 1.0},
        {"run_id": "../private-source"},
        {"run_id": "A" * 32},
        {"scenario": "custom"},
        {"scenario": []},
        {"operation": "restore"},
        {"operation": True},
        {"path": "/private-source"},
    ],
)
def test_invalid_action_never_echoes_rejected_input(replacement: dict[str, object]) -> None:
    """No arbitrary paths or alternative operations enter the local runner."""
    with pytest.raises(ServiceLabError, match=r"^invalid-action$"):
        parse_service_lab_action(service_lab_action_payload(_ACTION) | replacement)


@pytest.mark.parametrize(
    "replacement",
    [
        {"version": True},
        {"started": 1},
        {"healthy": 1},
        {"http_status": True},
        {"http_status": 200.0},
        {"http_status": 600},
        {"healthy": True, "http_status": 404},
        {"healthy": True, "http_status": 200, "error": "timeout"},
        {"error": "private-source"},
        {"error": []},
        {"unit": "\x1b[31m"},
        {"status": "a" * 2049},
        {"journal": "\uffff" * 2048, "unit": "\uffff" * 2048},
        {"path": "/private-source"},
    ],
)
def test_reports_reject_contradictions_and_unbounded_evidence(
    replacement: dict[str, object],
) -> None:
    """Strict bool/int separation and frame bounds apply before evidence is accepted."""
    payload = service_lab_report_payload(
        ServiceLabReport(
            run_id=_ACTION.run_id, scenario=_ACTION.scenario, started=True, healthy=False
        )
    )
    with pytest.raises(ServiceLabError, match=r"^invalid-report$"):
        parse_service_lab_report(payload | replacement, _ACTION)


@pytest.mark.parametrize("value", [None, [], "private-source", {}])
def test_incomplete_or_non_object_payloads_are_rejected(value: object) -> None:
    """Partial frames cannot acquire defaults that accidentally grant success."""
    with pytest.raises(ServiceLabError, match=r"^invalid-action$"):
        parse_service_lab_action(value)
    with pytest.raises(ServiceLabError, match=r"^invalid-report$"):
        parse_service_lab_report(value, _ACTION)
