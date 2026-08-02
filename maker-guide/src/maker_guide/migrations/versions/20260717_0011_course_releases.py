"""Move session release state from learners to courses."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op as alembic_operations

revision: str = "20260717_0011"
down_revision: str | None = "20260717_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create shared course releases and remove per-membership progress."""
    for statement in _UPGRADE_STATEMENTS:
        alembic_operations.execute(statement)


def downgrade() -> None:
    """Restore the previous per-membership session column."""
    for statement in _DOWNGRADE_STATEMENTS:
        alembic_operations.execute(statement)


_UPGRADE_STATEMENTS = (
    """create table course_releases (
    course_id text primary key,
    session_reached text not null,
    released_at text not null
)""",
    """create table cohort_memberships_new (
    handle text not null references learners(handle) on delete cascade,
    course_id text not null,
    joined_at text not null,
    primary key (handle, course_id)
)""",
    """insert into cohort_memberships_new (handle, course_id, joined_at)
select handle, course_id, joined_at from cohort_memberships""",
    "drop table cohort_memberships",
    "alter table cohort_memberships_new rename to cohort_memberships",
)

_DOWNGRADE_STATEMENTS = (
    """create table cohort_memberships_old (
    handle text not null references learners(handle) on delete cascade,
    course_id text not null,
    joined_at text not null,
    session_reached text null,
    primary key (handle, course_id)
)""",
    """insert into cohort_memberships_old (handle, course_id, joined_at, session_reached)
select cohort_memberships.handle, cohort_memberships.course_id, cohort_memberships.joined_at,
    course_releases.session_reached
from cohort_memberships
left join course_releases on course_releases.course_id = cohort_memberships.course_id""",
    "drop table cohort_memberships",
    "alter table cohort_memberships_old rename to cohort_memberships",
    "drop table course_releases",
)
