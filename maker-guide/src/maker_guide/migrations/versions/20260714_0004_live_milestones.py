"""Create live milestone completion table."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op as alembic_operations

revision: str = "20260714_0004"
down_revision: str | None = "20260713_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the live session milestone schema."""
    for statement in _CREATE_STATEMENTS:
        alembic_operations.execute(statement)


def downgrade() -> None:
    """Drop the live session milestone schema."""
    for statement in _DROP_STATEMENTS:
        alembic_operations.execute(statement)


_CREATE_STATEMENTS = (
    """
    create table live_milestone_completions (
        handle text not null,
        course_id text not null,
        session_id text not null,
        milestone_key text not null,
        completed_at text not null,
        marked_by text null,
        primary key (handle, course_id, session_id, milestone_key),
        foreign key (handle, course_id)
            references cohort_memberships(handle, course_id)
            on delete cascade
    )
    """,
    """
    create index live_milestone_completions_course_session
    on live_milestone_completions (course_id, session_id, milestone_key, handle)
    """,
)

_DROP_STATEMENTS = (
    "drop index live_milestone_completions_course_session",
    "drop table live_milestone_completions",
)
