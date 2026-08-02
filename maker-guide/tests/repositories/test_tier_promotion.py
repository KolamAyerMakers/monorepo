"""Tests for tier promotion repository functions."""

from __future__ import annotations

from pathlib import Path

from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.tier_promotion import (
    TierPromotion,
    list_tier_promotions,
    record_tier_promotion,
)
from tests.repositories.helpers import COURSE_ID, TIMESTAMP, write_learner


def test_tier_promotion_is_idempotent(migrated_database_path: Path) -> None:
    """Recording the same tier promotion twice stores one promotion."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        promotion = TierPromotion(
            handle="alice",
            course_id=COURSE_ID,
            tier_id="apprentice",
            promoted_at=TIMESTAMP,
            score_total=100,
        )

        record_tier_promotion(database_connection, promotion)
        record_tier_promotion(database_connection, promotion)

        assert list_tier_promotions(database_connection, "alice", COURSE_ID) == [promotion]
