"""Store learner POSIX UIDs for web-service routing."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op as alembic_operations

revision: str = "20260717_0010"
down_revision: str | None = "20260717_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the immutable POSIX uid captured during learner registration."""
    alembic_operations.execute("alter table learners add column uid integer null")


def downgrade() -> None:
    """Remove learner UIDs by rebuilding the SQLite table."""
    alembic_operations.execute(
        """
        create table learners_without_uid (
            handle text primary key,
            joined_at text not null,
            tagline text null,
            created_at text not null
        )
        """
    )
    alembic_operations.execute(
        """
        insert into learners_without_uid (handle, joined_at, tagline, created_at)
        select handle, joined_at, tagline, created_at from learners
        """
    )
    alembic_operations.execute("drop table learners")
    alembic_operations.execute("alter table learners_without_uid rename to learners")
