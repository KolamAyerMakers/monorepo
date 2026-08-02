"""Award score for peer thank-you records."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op as alembic_operations

revision: str = "20260717_0007"
down_revision: str | None = "20260717_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Backfill peer-thank score awards and enforce their source records."""
    for statement in _CREATE_STATEMENTS:
        alembic_operations.execute(statement)


def downgrade() -> None:
    """Remove peer-thank score guards without revoking awarded score."""
    for statement in _DROP_STATEMENTS:
        alembic_operations.execute(statement)


_CREATE_STATEMENTS = (
    """
    create unique index score_ledger_unique_peer_thank
    on score_ledger (handle, course_id, related_id)
    where reason = 'peer_thank_received'
        and related_type = 'peer_thank'
        and related_id is not null
    """,
    """
    insert or ignore into score_ledger
        (handle, course_id, amount, reason, related_type, related_id, created_at)
    select
        recipient_handle,
        course_id,
        10,
        'peer_thank_received',
        'peer_thank',
        cast(id as text),
        created_at
    from peer_thanks
    """,
    """
    create trigger score_ledger_peer_thank_source
    before insert on score_ledger
    when new.reason = 'peer_thank_received'
        and not exists (
            select 1
            from peer_thanks
            where cast(id as text) = new.related_id
                and recipient_handle = new.handle
                and course_id = new.course_id
        )
    begin
        select raise(abort, 'peer thank score requires its received thank');
    end
    """,
)

_DROP_STATEMENTS = (
    "drop trigger score_ledger_peer_thank_source",
    "drop index score_ledger_unique_peer_thank",
)
