"""Create durable peer thank-you records."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op as alembic_operations

revision: str = "20260717_0006"
down_revision: str | None = "20260715_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create course-scoped peer thank storage and quota guards."""
    for statement in _CREATE_STATEMENTS:
        alembic_operations.execute(statement)


def downgrade() -> None:
    """Drop peer thank storage and quota guards."""
    for statement in _DROP_STATEMENTS:
        alembic_operations.execute(statement)


_CREATE_STATEMENTS = (
    """
    create table peer_thanks (
        id integer primary key,
        giver_handle text not null,
        recipient_handle text not null,
        course_id text not null,
        reason text not null,
        thanked_on text not null,
        created_at text not null,
        check (giver_handle != recipient_handle),
        unique (giver_handle, course_id, thanked_on),
        foreign key (giver_handle, course_id)
            references cohort_memberships(handle, course_id)
            on delete cascade,
        foreign key (recipient_handle, course_id)
            references cohort_memberships(handle, course_id)
            on delete cascade
    )
    """,
    """
    create index peer_thanks_recipient_course
    on peer_thanks (recipient_handle, course_id, created_at)
    """,
    """
    create trigger peer_thanks_giver_recipient_limit
    before insert on peer_thanks
    when (
        select count(*)
        from peer_thanks
        where giver_handle = new.giver_handle
            and recipient_handle = new.recipient_handle
            and course_id = new.course_id
    ) >= 3
    begin
        select raise(abort, 'peer thank giver-recipient limit reached');
    end
    """,
    """
    create trigger peer_thanks_no_same_day_reciprocal
    before insert on peer_thanks
    when exists (
        select 1
        from peer_thanks
        where giver_handle = new.recipient_handle
            and recipient_handle = new.giver_handle
            and course_id = new.course_id
            and thanked_on = new.thanked_on
    )
    begin
        select raise(abort, 'peer thank same-day reciprocal is not allowed');
    end
    """,
)

_DROP_STATEMENTS = (
    "drop trigger peer_thanks_no_same_day_reciprocal",
    "drop trigger peer_thanks_giver_recipient_limit",
    "drop index peer_thanks_recipient_course",
    "drop table peer_thanks",
)
