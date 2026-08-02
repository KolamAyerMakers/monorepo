"""Tests for curriculum calendar export command."""

from __future__ import annotations

from typer.testing import CliRunner

from maker_guide.cli.calendar import app

_RUNNER = CliRunner()


def test_calendar_exports_table_by_default() -> None:
    """The default command output is a readable Rich table."""
    result = _RUNNER.invoke(app, ["lf2607"])

    assert result.exit_code == 0
    assert "Linux Foundations (lf2607)" in result.output
    assert "Date" in result.output
    assert "Type" in result.output
    assert "Session S1" not in result.output
    assert "2026-07-18" in result.output
    assert "session" in result.output
    assert "S1" in result.output
    assert "First contact: SSH" in result.output
    assert "2026-09-26" in result.output
    assert "S8" in result.output
    assert "Your own web service" in result.output


def test_calendar_exports_sessions_as_icalendar_events() -> None:
    """The calendar command emits importable all-day session events."""
    result = _RUNNER.invoke(app, ["lf2607", "-o", "ical"])

    assert result.exit_code == 0
    output = result.stdout_bytes.decode()

    assert output.split("\r\n")[:7] == [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Kolam Makers//maker-guide//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Linux Foundations",
        "X-WR-CALDESC:lf2607",
    ]
    assert "SUMMARY:Session S1: First contact: SSH and the lay of the land" in output
    assert "DTSTART;VALUE=DATE:20260718" in output
    assert "SUMMARY:Session S8: Your own web service" in output
    assert "DTSTART;VALUE=DATE:20260926" in output
    assert "SUMMARY:Quest" not in output
    assert output.endswith("END:VCALENDAR\r\n")


def test_calendar_exports_sessions_as_csv_rows() -> None:
    """The calendar command emits machine-readable comma-separated rows."""
    result = _RUNNER.invoke(app, ["lf2607", "-o", "csv"])

    assert result.exit_code == 0
    assert result.output.splitlines()[:4] == [
        "date,type,id,title",
        "2026-07-18,session,S1,First contact: SSH and the lay of the land",
        '2026-07-25,session,S2,"Files, editing, identity"',
        '2026-08-01,session,S3,"Streams, pipes, processes"',
    ]
    assert "quest" not in result.output
    assert '2026-10-24,session,S10,"Boss fight, demos, graduation"' in result.output


def test_calendar_rejects_unknown_curriculum() -> None:
    """The command accepts only known curriculum ids."""
    result = _RUNNER.invoke(app, ["missing-curriculum"])

    assert result.exit_code == 2
    assert "Unknown curriculum: missing-curriculum" in result.output


def test_calendar_rejects_unknown_output_format() -> None:
    """Typer validates the output format option."""
    result = _RUNNER.invoke(app, ["lf2607", "-o", "json"])

    assert result.exit_code == 2
    assert "Invalid value" in result.output
