"""Rename the ls manual-page comprehension quest."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op as alembic_operations

revision: str = "20260718_0014"
down_revision: str | None = "20260717_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Preserve learner quest state under the new identifier."""
    for statement in _UPGRADE_STATEMENTS:
        alembic_operations.execute(statement)


def downgrade() -> None:
    """Restore the previous quest identifier."""
    for statement in _DOWNGRADE_STATEMENTS:
        alembic_operations.execute(statement)


_UPGRADE_STATEMENTS = (
    "drop trigger quest_attempts_are_append_only",
    """update quest_assignments set quest_id = 'explain-ls'
    where course_id = 'lf2607' and quest_id = 'read-man-ls'""",
    """update quest_instances set quest_id = 'explain-ls'
    where course_id = 'lf2607' and quest_id = 'read-man-ls'""",
    """update quest_attempts set quest_id = 'explain-ls'
    where course_id = 'lf2607' and quest_id = 'read-man-ls'""",
    """update quest_completions set quest_id = 'explain-ls'
    where course_id = 'lf2607' and quest_id = 'read-man-ls'""",
    """update score_ledger set related_id = 'explain-ls'
    where course_id = 'lf2607' and related_type = 'quest' and related_id = 'read-man-ls'""",
    """create trigger quest_attempts_are_append_only
    before update on quest_attempts
    begin
        select raise(abort, 'quest attempts are append-only');
    end""",
)

_DOWNGRADE_STATEMENTS = (
    "drop trigger quest_attempts_are_append_only",
    """update quest_assignments set quest_id = 'read-man-ls'
    where course_id = 'lf2607' and quest_id = 'explain-ls'""",
    """update quest_instances set quest_id = 'read-man-ls'
    where course_id = 'lf2607' and quest_id = 'explain-ls'""",
    """update quest_attempts set quest_id = 'read-man-ls'
    where course_id = 'lf2607' and quest_id = 'explain-ls'""",
    """update quest_completions set quest_id = 'read-man-ls'
    where course_id = 'lf2607' and quest_id = 'explain-ls'""",
    """update score_ledger set related_id = 'read-man-ls'
    where course_id = 'lf2607' and related_type = 'quest' and related_id = 'explain-ls'""",
    """create trigger quest_attempts_are_append_only
    before update on quest_attempts
    begin
        select raise(abort, 'quest attempts are append-only');
    end""",
)
