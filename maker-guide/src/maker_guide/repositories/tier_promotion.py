"""Tier promotion repository functions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import cast


@dataclass(frozen=True, kw_only=True, slots=True)
class TierPromotion:
    """First time a learner reached a tier."""

    handle: str
    """Shared learner id."""
    course_id: str
    """Course id from the Python curriculum catalog."""
    tier_id: str
    """Tier id from the Python curriculum catalog."""
    promoted_at: str
    """ISO timestamp for when promotion was recorded."""
    score_total: int
    """Course score total at promotion time."""


def record_tier_promotion(
    database_connection: sqlite3.Connection,
    promotion: TierPromotion,
) -> None:
    """Idempotently record a tier promotion."""
    database_connection.execute(
        """
        insert or ignore into tier_promotions
            (handle, course_id, tier_id, promoted_at, score_total)
        values (?, ?, ?, ?, ?)
        """,
        (
            promotion.handle,
            promotion.course_id,
            promotion.tier_id,
            promotion.promoted_at,
            promotion.score_total,
        ),
    )


def list_tier_promotions(
    database_connection: sqlite3.Connection,
    handle: str,
    course_id: str,
) -> list[TierPromotion]:
    """Return learner tier promotions for a course."""
    promotion_records = cast(
        "list[tuple[str, str, str, str, int]]",
        database_connection.execute(
            """
            select handle, course_id, tier_id, promoted_at, score_total
            from tier_promotions
            where handle = ? and course_id = ?
            order by score_total, promoted_at
            """,
            (handle, course_id),
        ).fetchall(),
    )
    return [
        TierPromotion(
            handle=promotion_record[0],
            course_id=promotion_record[1],
            tier_id=promotion_record[2],
            promoted_at=promotion_record[3],
            score_total=promotion_record[4],
        )
        for promotion_record in promotion_records
    ]
