"""Drop redundant manual live milestone state."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op as alembic_operations

revision: str = "20260717_0012"
down_revision: str | None = "20260717_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Remove manual state superseded by objective and quest completions."""
    alembic_operations.execute("drop table live_milestone_completions")


def downgrade() -> None:
    """Restore the removed manual milestone table."""
    alembic_operations.execute(
        """create table live_milestone_completions (
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
    )""",
    )
    alembic_operations.execute(
        """create index live_milestone_completions_course_session
        on live_milestone_completions (course_id, session_id, milestone_key, handle)""",
    )
