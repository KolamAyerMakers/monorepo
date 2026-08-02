"""Curriculum calendar export command."""

from __future__ import annotations

from collections.abc import Iterable
from csv import writer as csv_writer
from datetime import date, timedelta
from enum import StrEnum
from io import StringIO
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from maker_guide.curriculum.catalogs import course_by_id
from maker_guide.curriculum.models import Course, Session

_CALENDAR_DOMAIN = "maker-guide.kolamayermakers.org"
_ICALENDAR_LINE_LIMIT = 75
_ICALENDAR_CONTINUATION_LIMIT = _ICALENDAR_LINE_LIMIT - 1
app = typer.Typer(
    add_completion=False,
    help="Export a maker-guide curriculum calendar.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)


class OutputFormat(StrEnum):
    """Supported calendar output formats."""

    table = "table"
    ical = "ical"
    csv = "csv"


def main() -> None:
    """Run the curriculum calendar export command."""
    app()


@app.command()
def export(
    curriculum: Annotated[str, typer.Argument(help="Curriculum id to export.")],
    output_format: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format."),
    ] = OutputFormat.table,
) -> None:
    """Export a curriculum calendar."""
    course = course_by_id(curriculum)
    if course is None:
        Console(stderr=True).print(f"[red]Unknown curriculum: {curriculum}[/red]")
        raise typer.Exit(2)
    if output_format == OutputFormat.ical:
        _write_icalendar(course, Console())
        return
    if output_format == OutputFormat.csv:
        _write_csv(course, Console())
        return
    _write_table(course, Console())


def _write_icalendar(course: Course, console: Console) -> None:
    for line in _calendar_lines(course):
        for folded_line in _fold_icalendar_line(line):
            console.out(folded_line, end="\r\n")


def _write_table(course: Course, console: Console) -> None:
    table = Table(title=f"{course.title} ({course.id})")
    table.add_column("Date", no_wrap=True)
    table.add_column("Type", no_wrap=True)
    table.add_column("ID", no_wrap=True)
    table.add_column("Title")
    for event_date, event_type, identifier, title in sorted(_calendar_table_rows(course)):
        table.add_row(event_date.isoformat(), event_type, identifier, title)
    console.print(table)


def _write_csv(course: Course, console: Console) -> None:
    output_stream = StringIO()
    calendar_writer = csv_writer(output_stream, lineterminator="\n")
    calendar_writer.writerow(("date", "type", "id", "title"))
    for event_date, event_type, identifier, title in sorted(_calendar_table_rows(course)):
        calendar_writer.writerow((event_date.isoformat(), event_type, identifier, title))
    console.out(output_stream.getvalue(), end="")


def _calendar_table_rows(course: Course) -> Iterable[tuple[date, str, str, str]]:
    for session in course.sessions:
        yield session.date, "session", session.id, session.title


def _calendar_lines(course: Course) -> Iterable[str]:
    yield "BEGIN:VCALENDAR"
    yield "VERSION:2.0"
    yield "PRODID:-//Kolam Makers//maker-guide//EN"
    yield "CALSCALE:GREGORIAN"
    yield "METHOD:PUBLISH"
    yield f"X-WR-CALNAME:{_escape_icalendar_text(course.title)}"
    yield f"X-WR-CALDESC:{_escape_icalendar_text(course.id)}"
    for session in course.sessions:
        yield from _session_event_lines(course, session)
    yield "END:VCALENDAR"


def _session_event_lines(course: Course, session: Session) -> Iterable[str]:
    yield from _event_lines(
        uid=f"{course.id}-session-{session.id}@{_CALENDAR_DOMAIN}",
        event_date=session.date,
        stamp_date=course.starts_on,
        summary=f"Session {session.id}: {session.title}",
        description="\n".join(
            (
                f"Session {session.id}",
                "Objectives:",
                *_prefixed_lines(session.learning_objectives),
            ),
        ),
    )


def _event_lines(
    *,
    uid: str,
    event_date: date,
    stamp_date: date,
    summary: str,
    description: str,
) -> Iterable[str]:
    yield "BEGIN:VEVENT"
    yield f"UID:{_escape_icalendar_text(uid)}"
    yield f"DTSTAMP:{stamp_date:%Y%m%d}T000000Z"
    yield f"DTSTART;VALUE=DATE:{event_date:%Y%m%d}"
    yield f"DTEND;VALUE=DATE:{event_date + timedelta(days=1):%Y%m%d}"
    yield f"SUMMARY:{_escape_icalendar_text(summary)}"
    yield f"DESCRIPTION:{_escape_icalendar_text(description)}"
    yield "TRANSP:TRANSPARENT"
    yield "END:VEVENT"


def _prefixed_lines(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(f"- {value}" for value in values)


def _escape_icalendar_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _fold_icalendar_line(line: str) -> tuple[str, ...]:
    if len(line) <= _ICALENDAR_LINE_LIMIT:
        return (line,)

    folded_lines: list[str] = []
    remaining_line = line
    while len(remaining_line) > _ICALENDAR_LINE_LIMIT:
        if folded_lines:
            folded_lines.append(f" {remaining_line[:_ICALENDAR_CONTINUATION_LIMIT]}")
            remaining_line = remaining_line[_ICALENDAR_CONTINUATION_LIMIT:]
        else:
            folded_lines.append(remaining_line[:_ICALENDAR_LINE_LIMIT])
            remaining_line = remaining_line[_ICALENDAR_LINE_LIMIT:]
    if remaining_line:
        folded_lines.append(f" {remaining_line}" if folded_lines else remaining_line)
    return tuple(folded_lines)
