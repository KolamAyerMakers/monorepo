"""Tests for IRC peer thank-you handling."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from maker_guide.chat.contract import (
    ChatDependencies,
    ChatRequest,
    ChatResponse,
    CliChatContext,
    IrcChatContext,
)
from maker_guide.chat.service import handle_chat_request
from maker_guide.curriculum.catalogs import DEFAULT_CATALOG as CATALOG
from maker_guide.repositories.cohort_membership import CohortMembership, upsert_membership
from maker_guide.repositories.course_release import CourseRelease, upsert_course_release
from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.learner import Learner, upsert_learner
from maker_guide.repositories.outbox_item import list_pending_outbox_items
from maker_guide.repositories.score_ledger import (
    ScoreLedgerEntry,
    add_score_entry,
    total_score_for_course,
)


def test_thank_records_reason_audit_and_projection_work(migrated_database_path: Path) -> None:
    """A valid thank is durable, auditable, and queued for projection."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, "alice")
        _write_member(database_connection, "bob")

        response = _thank(database_connection, "alice", "bob", "Explained SSH permissions")

        assert response.text == "Thank-you recorded. bob earned 10 points."
        assert database_connection.execute(
            "select giver_handle, recipient_handle, reason, thanked_on from peer_thanks",
        ).fetchall() == [("alice", "bob", "Explained SSH permissions", "2026-07-19")]
        assert database_connection.execute(
            """
            select event_type, handle, source
            from audit_events
            where event_type = 'peer_thank_sent'
            """,
        ).fetchall() == [("peer_thank_sent", "alice", "irc")]
        assert database_connection.execute(
            """
            select amount, reason, related_type, related_id
            from score_ledger
            where handle = 'bob'
            """,
        ).fetchall() == [(10, "peer_thank_received", "peer_thank", "1")]
        assert total_score_for_course(database_connection, "bob", CATALOG.course.id) == 10
        assert [item.payload for item in list_pending_outbox_items(database_connection, 10)] == [
            {
                "course_id": CATALOG.course.id,
                "handle": "bob",
                "reason": "peer_thank_received",
            },
        ]


def test_thank_promotion_has_a_public_announcement(migrated_database_path: Path) -> None:
    """A thank that crosses a tier threshold returns a public promotion notice."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, "alice")
        _write_member(database_connection, "bob")
        add_score_entry(
            database_connection,
            ScoreLedgerEntry(
                id=None,
                handle="bob",
                course_id=CATALOG.course.id,
                amount=490,
                reason="test",
                related_type="test",
                related_id="before-thank",
                created_at="2026-07-19T08:00:00Z",
            ),
        )

        response = _thank(database_connection, "alice", "bob", "Explained SSH permissions")

        assert response.public_announcements == ("bob became an apprentice",)
        assert database_connection.execute(
            "select source from audit_events where event_type = 'tier_promoted'",
        ).fetchall() == [("irc",)]


def test_cli_thank_records_cli_audit_provenance(migrated_database_path: Path) -> None:
    """CLI thanks retain their transport in thank and promotion audit records."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, "alice")
        _write_member(database_connection, "bob")
        add_score_entry(
            database_connection,
            ScoreLedgerEntry(
                id=None,
                handle="bob",
                course_id=CATALOG.course.id,
                amount=490,
                reason="test",
                related_type="test",
                related_id="before-thank",
                created_at="2026-07-19T08:00:00Z",
            ),
        )

        handle_chat_request(
            ChatRequest(
                context=CliChatContext(username="alice", terminal="xterm", ssh_connection=None),
                visibility="private",
                text="thank bob Explained SSH permissions",
            ),
            ChatDependencies(
                database_connection=database_connection,
                catalog=CATALOG,
                bot_name="guide-test",
                timestamp_factory=lambda: "2026-07-19T09:00:00Z",
            ),
        )

        assert database_connection.execute(
            "select source from audit_events where event_type = 'peer_thank_sent'",
        ).fetchall() == [("cli",)]
        assert database_connection.execute(
            "select source from audit_events where event_type = 'tier_promoted'",
        ).fetchall() == [("cli",)]


@pytest.mark.parametrize(
    ("recipient_handle", "reason", "expected_text"),
    [
        ("alice", "I helped myself", "You cannot thank yourself."),
        ("nobody", "Explained SSH permissions", "That learner is not in this course."),
        ("bob", "", "Use `!thank nickname reason` and explain what they helped with."),
    ],
)
def test_thank_rejects_invalid_recipient_or_reason(
    migrated_database_path: Path,
    recipient_handle: str,
    reason: str,
    expected_text: str,
) -> None:
    """Invalid thank commands do not create durable thank records."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, "alice")
        _write_member(database_connection, "bob")

        response = _thank(database_connection, "alice", recipient_handle, reason)

        assert response.text == expected_text
        assert database_connection.execute("select count(*) from peer_thanks").fetchone() == (0,)


def test_thank_enforces_daily_pair_and_reciprocal_quotas(migrated_database_path: Path) -> None:
    """Course-local daily, pair, and reciprocal limits are enforced before recording."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, "alice")
        _write_member(database_connection, "bob")
        _write_member(database_connection, "cara")

        assert _thank(
            database_connection,
            "alice",
            "bob",
            "Explained SSH permissions",
        ).text.startswith(
            "Thank-you recorded",
        )
        assert _thank(database_connection, "alice", "cara", "Explained groups").text == (
            "You can send one thank-you per day."
        )
        assert _thank(database_connection, "bob", "alice", "Explained permissions").text == (
            "You cannot exchange thank-yous with the same learner on one day."
        )

        for day in ("2026-07-20", "2026-07-21"):
            assert _thank(
                database_connection,
                "alice",
                "bob",
                "Explained SSH permissions",
                f"{day}T09:00:00Z",
            ).text.startswith("Thank-you recorded")
        assert (
            _thank(
                database_connection,
                "alice",
                "bob",
                "Explained SSH permissions",
                "2026-07-22T09:00:00Z",
            ).text
            == "You have already thanked bob 3 times."
        )


def test_peer_thank_database_guards_reject_direct_invalid_inserts(
    migrated_database_path: Path,
) -> None:
    """Database triggers protect quotas when callers bypass the chat service."""
    with connect_database(migrated_database_path) as database_connection:
        _write_member(database_connection, "alice")
        _write_member(database_connection, "bob")
        database_connection.execute(
            """
            insert into peer_thanks
                (giver_handle, recipient_handle, course_id, reason, thanked_on, created_at)
            values (
                'alice', 'bob', ?, 'Explained SSH permissions', '2026-07-19',
                '2026-07-19T09:00:00Z'
            )
            """,
            (CATALOG.course.id,),
        )

        with pytest.raises(sqlite3.IntegrityError, match="same-day reciprocal"):
            database_connection.execute(
                """
                insert into peer_thanks
                    (giver_handle, recipient_handle, course_id, reason, thanked_on, created_at)
                values ('bob', 'alice', ?, 'Explained groups', '2026-07-19', '2026-07-19T10:00:00Z')
                """,
                (CATALOG.course.id,),
            )


def _thank(
    database_connection: sqlite3.Connection,
    giver_handle: str,
    recipient_handle: str,
    reason: str,
    timestamp: str = "2026-07-19T09:00:00Z",
) -> ChatResponse:
    text = f"thank {recipient_handle} {reason}".rstrip()
    return handle_chat_request(
        ChatRequest(
            context=IrcChatContext(
                nickname=giver_handle,
                target="#kolam",
                reply_target="#kolam",
            ),
            visibility="public",
            text=text,
        ),
        ChatDependencies(
            database_connection=database_connection,
            catalog=CATALOG,
            bot_name="guide-test",
            timestamp_factory=lambda: timestamp,
        ),
    )


def _write_member(database_connection: sqlite3.Connection, handle: str) -> None:
    upsert_learner(
        database_connection,
        Learner(
            handle=handle,
            joined_at="2026-07-18T09:00:00Z",
            tagline=None,
            created_at="2026-07-18T09:00:00Z",
        ),
    )
    upsert_membership(
        database_connection,
        CohortMembership(
            handle=handle,
            course_id=CATALOG.course.id,
            joined_at="2026-07-18T09:00:00Z",
        ),
    )
    upsert_course_release(
        database_connection,
        CourseRelease(
            course_id=CATALOG.course.id,
            session_reached="S1",
            released_at="2026-07-18T09:00:00Z",
        ),
    )
