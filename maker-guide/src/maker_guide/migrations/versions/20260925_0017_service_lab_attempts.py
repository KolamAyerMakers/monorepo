"""Persist learner service troubleshooting attempts without rewriting old credit."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op as alembic_operations

revision: str = "20260925_0017"
down_revision: str | None = "20260801_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Reserve one stable run per learner objective before local execution."""
    alembic_operations.execute("""
        create table service_lab_attempts (
            handle text not null references learners(handle) on delete cascade,
            course_id text not null,
            session_id text not null,
            objective_id text not null,
            run_id text not null unique,
            scenario text not null,
            message_index integer not null,
            created_at text not null,
            started_at text,
            primary key (handle, course_id, session_id, objective_id)
        )
    """)


def downgrade() -> None:
    """Remove only local-lab coordination records."""
    alembic_operations.execute("drop table service_lab_attempts")
