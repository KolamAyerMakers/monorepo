"""Add rank eligibility to cohort memberships."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op as alembic_operations

revision: str = "20260719_0015"
down_revision: str | None = "20260718_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Make existing and new memberships rank eligible by default."""
    alembic_operations.execute(
        "alter table cohort_memberships add column rank_eligible integer not null default 1",
    )


def downgrade() -> None:
    """Remove rank eligibility from cohort memberships."""
    for statement in _DOWNGRADE_STATEMENTS:
        alembic_operations.execute(statement)


_DOWNGRADE_STATEMENTS = (
    """create table cohort_memberships_old (
    handle text not null references learners(handle) on delete cascade,
    course_id text not null,
    joined_at text not null,
    primary key (handle, course_id)
)""",
    """insert into cohort_memberships_old (handle, course_id, joined_at)
select handle, course_id, joined_at from cohort_memberships""",
    "drop table cohort_memberships",
    "alter table cohort_memberships_old rename to cohort_memberships",
)
