"""Deduplicate replayed shell-hook observations."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op as alembic_operations

revision: str = "20260717_0013"
down_revision: str | None = "20260717_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Store stable event identities without invalidating legacy observations."""
    alembic_operations.execute("alter table command_observations add column event_id text null")
    alembic_operations.execute(
        """
        create unique index command_observations_event_id
        on command_observations (event_id) where event_id is not null
        """,
    )


def downgrade() -> None:
    """Remove event identity deduplication."""
    alembic_operations.execute("drop index command_observations_event_id")
    alembic_operations.execute("alter table command_observations drop column event_id")
