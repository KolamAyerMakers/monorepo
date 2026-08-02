"""Repository functions for course peer thank-you records."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import cast

from maker_guide.repositories.helpers import last_inserted_id


@dataclass(frozen=True, kw_only=True, slots=True)
class PeerThank:
    """One learner acknowledgement of another learner's help."""

    id: int | None
    giver_handle: str
    recipient_handle: str
    course_id: str
    reason: str
    thanked_on: str
    created_at: str


def add_peer_thank(database_connection: sqlite3.Connection, peer_thank: PeerThank) -> int:
    """Store one peer thank and return its database id."""
    return last_inserted_id(
        database_connection.execute(
            """
            insert into peer_thanks
                (giver_handle, recipient_handle, course_id, reason, thanked_on, created_at)
            values (?, ?, ?, ?, ?, ?)
            """,
            (
                peer_thank.giver_handle,
                peer_thank.recipient_handle,
                peer_thank.course_id,
                peer_thank.reason,
                peer_thank.thanked_on,
                peer_thank.created_at,
            ),
        ),
    )


def count_peer_thanks_between(
    database_connection: sqlite3.Connection,
    giver_handle: str,
    recipient_handle: str,
    course_id: str,
) -> int:
    """Return thank count from one learner to another in a course."""
    return cast(
        "int",
        database_connection.execute(
            """
            select count(*)
            from peer_thanks
            where giver_handle = ? and recipient_handle = ? and course_id = ?
            """,
            (giver_handle, recipient_handle, course_id),
        ).fetchone()[0],
    )


def has_peer_thank_on_date(
    database_connection: sqlite3.Connection,
    giver_handle: str,
    recipient_handle: str,
    course_id: str,
    thanked_on: str,
) -> bool:
    """Return whether a thank exists for a directed pair on one local date."""
    return (
        database_connection.execute(
            """
            select 1
            from peer_thanks
            where giver_handle = ?
                and recipient_handle = ?
                and course_id = ?
                and thanked_on = ?
            """,
            (giver_handle, recipient_handle, course_id, thanked_on),
        ).fetchone()
        is not None
    )


def has_sent_peer_thank_on_date(
    database_connection: sqlite3.Connection,
    giver_handle: str,
    course_id: str,
    thanked_on: str,
) -> bool:
    """Return whether a learner has already sent a thank on one local date."""
    return (
        database_connection.execute(
            """
            select 1
            from peer_thanks
            where giver_handle = ? and course_id = ? and thanked_on = ?
            """,
            (giver_handle, course_id, thanked_on),
        ).fetchone()
        is not None
    )


def list_peer_thanks_by_recipient(
    database_connection: sqlite3.Connection,
    course_id: str,
) -> dict[str, tuple[PeerThank, ...]]:
    """Return each course learner's received thank-yous, newest first."""
    thank_records = cast(
        "list[tuple[int, str, str, str, str, str, str]]",
        database_connection.execute(
            """
            select id, giver_handle, recipient_handle, course_id, reason, thanked_on, created_at
            from peer_thanks
            where course_id = ?
            order by recipient_handle, created_at desc, id desc
            """,
            (course_id,),
        ).fetchall(),
    )
    thanks_by_recipient: dict[str, list[PeerThank]] = {}
    for thank_record in thank_records:
        peer_thank = PeerThank(
            id=thank_record[0],
            giver_handle=thank_record[1],
            recipient_handle=thank_record[2],
            course_id=thank_record[3],
            reason=thank_record[4],
            thanked_on=thank_record[5],
            created_at=thank_record[6],
        )
        thanks_by_recipient.setdefault(peer_thank.recipient_handle, []).append(peer_thank)
    return {
        recipient_handle: tuple(peer_thanks)
        for recipient_handle, peer_thanks in thanks_by_recipient.items()
    }
