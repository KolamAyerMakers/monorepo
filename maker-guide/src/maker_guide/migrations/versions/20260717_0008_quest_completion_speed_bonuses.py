"""Award first completion bonuses for each quest."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op as alembic_operations

revision: str = "20260717_0008"
down_revision: str | None = "20260717_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add query and integrity support for quest completion bonuses."""
    for statement in _CREATE_STATEMENTS:
        alembic_operations.execute(statement)


def downgrade() -> None:
    """Remove quest completion bonus guards without revoking awards."""
    for statement in _DROP_STATEMENTS:
        alembic_operations.execute(statement)


_CREATE_STATEMENTS = (
    "create index quest_completions_course_quest on quest_completions (course_id, quest_id)",
    """
    create unique index score_ledger_unique_quest_completion_speed_bonus
    on score_ledger (handle, course_id, related_id)
    where reason = 'quest_completion_speed_bonus'
        and related_type = 'quest'
        and related_id is not null
    """,
    """
    create trigger score_ledger_quest_completion_speed_bonus_source
    before insert on score_ledger
    when new.reason = 'quest_completion_speed_bonus'
        and not exists (
            select 1
            from quest_completions
            where handle = new.handle
                and course_id = new.course_id
                and quest_id = new.related_id
        )
    begin
        select raise(abort, 'quest speed bonus requires its completed quest');
    end
    """,
)

_DROP_STATEMENTS = (
    "drop trigger score_ledger_quest_completion_speed_bonus_source",
    "drop index score_ledger_unique_quest_completion_speed_bonus",
    "drop index quest_completions_course_quest",
)
