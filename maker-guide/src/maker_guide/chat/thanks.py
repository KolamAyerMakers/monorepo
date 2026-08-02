"""Peer thank-you command handling."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from maker_guide.chat.contract import ChatDependencies
from maker_guide.chat.intents import thank_arguments
from maker_guide.progress.service import record_tier_promotions
from maker_guide.repositories.audit_event import AuditEvent, append_audit_event
from maker_guide.repositories.cohort_membership import get_membership
from maker_guide.repositories.outbox_item import enqueue_outbox_item, projection_outbox_item
from maker_guide.repositories.peer_thank import (
    PeerThank,
    add_peer_thank,
    count_peer_thanks_between,
    has_peer_thank_on_date,
    has_sent_peer_thank_on_date,
)
from maker_guide.repositories.score_ledger import (
    ScoreLedgerEntry,
    add_score_entry,
    total_score_for_course,
)
from maker_guide.repositories.tier_promotion import TierPromotion

_MAX_REASON_LENGTH = 280
_MAX_THANKS_PER_PAIR = 3


def thank_response(  # noqa: PLR0911 - Learner-facing validation failures are direct responses.
    dependencies: ChatDependencies,
    giver_handle: str,
    text: str,
    timestamp: str,
    source: str,
) -> tuple[str, tuple[TierPromotion, ...]]:
    """Record one peer thank or return a concise command error."""
    arguments = thank_arguments(text)
    if arguments is None:
        return "Use `!thank nickname reason` and explain what they helped with.", ()
    recipient_handle, reason = arguments
    if len(reason) > _MAX_REASON_LENGTH:
        return f"Keep the thank-you reason under {_MAX_REASON_LENGTH} characters.", ()
    if recipient_handle == giver_handle:
        return "You cannot thank yourself.", ()

    course_id = dependencies.catalog.course.id
    if get_membership(dependencies.database_connection, giver_handle, course_id) is None:
        return "You are not enrolled in this course.", ()
    if get_membership(dependencies.database_connection, recipient_handle, course_id) is None:
        return "That learner is not in this course.", ()
    thanked_on = _course_local_date(timestamp, dependencies.catalog.course.timezone)
    if has_peer_thank_on_date(
        dependencies.database_connection,
        recipient_handle,
        giver_handle,
        course_id,
        thanked_on,
    ):
        return "You cannot exchange thank-yous with the same learner on one day.", ()
    if has_sent_peer_thank_on_date(
        dependencies.database_connection,
        giver_handle,
        course_id,
        thanked_on,
    ):
        return "You can send one thank-you per day.", ()
    if (
        count_peer_thanks_between(
            dependencies.database_connection,
            giver_handle,
            recipient_handle,
            course_id,
        )
        >= _MAX_THANKS_PER_PAIR
    ):
        return f"You have already thanked {recipient_handle} {_MAX_THANKS_PER_PAIR} times.", ()

    previous_score_total = total_score_for_course(
        dependencies.database_connection,
        recipient_handle,
        course_id,
    )
    try:
        peer_thank_id = add_peer_thank(
            dependencies.database_connection,
            PeerThank(
                id=None,
                giver_handle=giver_handle,
                recipient_handle=recipient_handle,
                course_id=course_id,
                reason=reason,
                thanked_on=thanked_on,
                created_at=timestamp,
            ),
        )
    except sqlite3.IntegrityError as error:
        return _quota_error_text(error), ()
    add_score_entry(
        dependencies.database_connection,
        ScoreLedgerEntry(
            id=None,
            handle=recipient_handle,
            course_id=course_id,
            amount=10,
            reason="peer_thank_received",
            related_type="peer_thank",
            related_id=str(peer_thank_id),
            created_at=timestamp,
        ),
    )
    tier_promotions = record_tier_promotions(
        dependencies.database_connection,
        dependencies.catalog,
        recipient_handle,
        timestamp,
        source,
        previous_score_total,
        total_score_for_course(dependencies.database_connection, recipient_handle, course_id),
    )
    append_audit_event(
        dependencies.database_connection,
        AuditEvent(
            event_type="peer_thank_sent",
            handle=giver_handle,
            source=source,
            created_at=timestamp,
            payload={
                "course_id": course_id,
                "recipient_handle": recipient_handle,
                "reason": reason,
                "thanked_on": thanked_on,
            },
        ),
    )
    enqueue_outbox_item(
        dependencies.database_connection,
        projection_outbox_item(
            handle=recipient_handle,
            course_id=course_id,
            created_at=timestamp,
            reason="peer_thank_received",
        ),
    )
    return f"Thank-you recorded. {recipient_handle} earned 10 points.", tier_promotions


def _course_local_date(timestamp: str, timezone: str) -> str:
    return (
        datetime.fromisoformat(timestamp)
        .astimezone(
            ZoneInfo(timezone),
        )
        .date()
        .isoformat()
    )


def _quota_error_text(error: sqlite3.IntegrityError) -> str:
    error_text = str(error)
    if "giver-recipient limit" in error_text:
        return "You have already thanked that learner 3 times."
    if "same-day reciprocal" in error_text:
        return "You cannot exchange thank-yous with the same learner on one day."
    if "peer_thanks.giver_handle, peer_thanks.course_id, peer_thanks.thanked_on" in error_text:
        return "You can send one thank-you per day."
    raise error
