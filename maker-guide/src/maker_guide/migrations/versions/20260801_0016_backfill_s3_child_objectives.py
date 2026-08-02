"""Backfill split S3 objective completions."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op as alembic_operations

revision: str = "20260801_0016"
down_revision: str | None = "20260719_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Copy parent completion evidence and base scores to each child objective."""
    alembic_operations.execute(_BACKFILL_STATEMENT)
    alembic_operations.execute(_BACKFILL_SCORE_STATEMENT)


def downgrade() -> None:
    """Delete the S3 child completions and scores introduced by this migration."""
    alembic_operations.execute(_DELETE_SCORE_STATEMENT)
    alembic_operations.execute(_DELETE_STATEMENT)


_BACKFILL_STATEMENT = """
insert or ignore into session_objective_completions
    (handle, course_id, session_id, objective_id, completed_at, evidence_json)
select
    completion.handle,
    completion.course_id,
    completion.session_id,
    objective_mapping.child_id,
    completion.completed_at,
    completion.evidence_json
from session_objective_completions as completion
join (
    select 'make-first-pipe' as parent_id, 'name-stdout-descriptor' as child_id
    union all select 'make-first-pipe', 'name-stdin-descriptor'
    union all select 'combine-and-copy-streams', 'read-redirections-left-to-right'
    union all select 'combine-and-copy-streams', 'route-stderr-to-stdout-destination'
    union all select 'read-process-table', 'describe-running-process'
    union all select 'read-process-table', 'report-process-pair'
) as objective_mapping on objective_mapping.parent_id = completion.objective_id
where completion.course_id = 'lf2607' and completion.session_id = 'S3'
"""

_BACKFILL_SCORE_STATEMENT = """
insert or ignore into score_ledger
    (handle, course_id, amount, reason, related_type, related_id, created_at)
select
    handle,
    course_id,
    50,
    'session_objective_completed',
    'session_objective',
    session_id || ':' || objective_id,
    completed_at
from session_objective_completions
where course_id = 'lf2607'
    and session_id = 'S3'
    and objective_id in (
        'name-stdout-descriptor',
        'name-stdin-descriptor',
        'read-redirections-left-to-right',
        'route-stderr-to-stdout-destination',
        'describe-running-process',
        'report-process-pair'
    )
"""

_DELETE_SCORE_STATEMENT = """
delete from score_ledger
where course_id = 'lf2607'
    and reason = 'session_objective_completed'
    and related_type = 'session_objective'
    and related_id in (
        select 'S3:' || objective_id
        from session_objective_completions
        where course_id = 'lf2607'
            and session_id = 'S3'
            and objective_id in (
                'name-stdout-descriptor',
                'name-stdin-descriptor',
                'read-redirections-left-to-right',
                'route-stderr-to-stdout-destination',
                'describe-running-process',
                'report-process-pair'
            )
    )
"""

_DELETE_STATEMENT = """
delete from session_objective_completions
where course_id = 'lf2607'
    and session_id = 'S3'
    and objective_id in (
        'name-stdout-descriptor',
        'name-stdin-descriptor',
        'read-redirections-left-to-right',
        'route-stderr-to-stdout-destination',
        'describe-running-process',
        'report-process-pair'
    )
"""
