"""Rename Linux Foundations course id."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op as alembic_operations
from sqlalchemy import text

revision: str = "20260713_0003"
down_revision: str | None = "20260610_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PREVIOUS_COURSE_ID = "linux-foundations-2026-07"
_CURRENT_COURSE_ID = "lf2607"
_COURSE_ID_TABLES = (
    "cohort_memberships",
    "quest_assignments",
    "quest_instances",
    "quest_attempts",
    "quest_completions",
    "score_ledger",
    "tier_promotions",
    "command_observations",
    "llm_audit_logs",
)


def upgrade() -> None:
    """Move persisted course state to the current short course id."""
    _rename_course_id(_PREVIOUS_COURSE_ID, _CURRENT_COURSE_ID)


def downgrade() -> None:
    """Restore the previous course id."""
    _rename_course_id(_CURRENT_COURSE_ID, _PREVIOUS_COURSE_ID)


def _rename_course_id(previous_course_id: str, current_course_id: str) -> None:
    database_connection = alembic_operations.get_bind()
    database_connection.execute(text("drop trigger quest_attempts_are_append_only"))
    for table_name in _COURSE_ID_TABLES:
        database_connection.execute(
            text(
                "update "  # noqa: S608 - migration table names are hard-coded.
                + table_name
                + " set course_id = :current_course_id where course_id = :previous_course_id",
            ),
            {
                "current_course_id": current_course_id,
                "previous_course_id": previous_course_id,
            },
        )
    database_connection.execute(
        text(
            """
        update group_grants
        set group_name = :current_course_id,
            reason = case
                when reason = :previous_reason then :current_reason
                else reason
            end
        where group_name = :previous_course_id
        """,
        ),
        {
            "current_course_id": current_course_id,
            "current_reason": f"course:{current_course_id}",
            "previous_course_id": previous_course_id,
            "previous_reason": f"course:{previous_course_id}",
        },
    )
    database_connection.execute(
        text(
            """
            create trigger quest_attempts_are_append_only
            before update on quest_attempts
            begin
                select raise(abort, 'quest attempts are append-only');
            end
            """,
        ),
    )
