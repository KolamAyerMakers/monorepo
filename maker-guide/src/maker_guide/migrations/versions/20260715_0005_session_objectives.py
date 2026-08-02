"""Create durable session objective completions."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op as alembic_operations

revision: str = "20260715_0005"
down_revision: str | None = "20260714_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create objective completion storage."""
    alembic_operations.execute(
        """create table session_objective_completions (
        handle text not null, course_id text not null, session_id text not null,
        objective_id text not null, completed_at text not null, evidence_json text not null,
        primary key (handle, course_id, session_id, objective_id),
        foreign key (handle, course_id) references cohort_memberships(handle, course_id)
            on delete cascade)""",
    )


def downgrade() -> None:
    """Drop objective completion storage."""
    alembic_operations.execute("drop table session_objective_completions")
