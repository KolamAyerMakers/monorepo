"""Create restricted LLM audit log table."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op as alembic_operations

revision: str = "20260610_0002"
down_revision: str | None = "20260529_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the restricted full LLM audit log schema."""
    for statement in _CREATE_STATEMENTS:
        alembic_operations.execute(statement)


def downgrade() -> None:
    """Drop the restricted full LLM audit log schema."""
    for statement in _DROP_STATEMENTS:
        alembic_operations.execute(statement)


_CREATE_STATEMENTS = (
    """
    create table llm_audit_logs (
        id integer primary key,
        handle text not null references learners(handle) on delete cascade,
        course_id text not null,
        source text not null,
        created_at text not null,
        provider text not null,
        model text not null,
        status text not null,
        request_json text not null,
        response_json text not null,
        expires_at text not null
    )
    """,
    """
    create index llm_audit_logs_handle_created
    on llm_audit_logs (handle, created_at)
    """,
    """
    create index llm_audit_logs_expires
    on llm_audit_logs (expires_at, id)
    """,
)

_DROP_STATEMENTS = (
    "drop index llm_audit_logs_expires",
    "drop index llm_audit_logs_handle_created",
    "drop table llm_audit_logs",
)
