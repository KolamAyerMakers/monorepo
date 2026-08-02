"""Course enrollment service flows."""

from __future__ import annotations

import sqlite3

from maker_guide.enrollment.models import EnrollmentInput, EnrollmentResult, EnrollmentServiceError
from maker_guide.repositories.audit_event import AuditEvent, append_audit_event
from maker_guide.repositories.cohort_membership import (
    CohortMembership,
    get_membership,
    upsert_membership,
)
from maker_guide.repositories.helpers import transaction
from maker_guide.repositories.learner import get_learner
from maker_guide.repositories.outbox_item import enqueue_outbox_item, projection_outbox_item


def enroll(
    database_connection: sqlite3.Connection,
    enrollment_input: EnrollmentInput,
) -> EnrollmentResult:
    """Enroll an existing learner into a course."""
    with transaction(database_connection):
        if get_learner(database_connection, enrollment_input.handle) is None:
            raise EnrollmentServiceError("learner identity does not exist")

        existing_membership = get_membership(
            database_connection,
            enrollment_input.handle,
            enrollment_input.course_id,
        )
        if existing_membership is not None:
            return EnrollmentResult(membership=existing_membership, created=False)

        membership = CohortMembership(
            handle=enrollment_input.handle,
            course_id=enrollment_input.course_id,
            joined_at=enrollment_input.joined_at,
            rank_eligible=enrollment_input.rank_eligible,
        )
        upsert_membership(
            database_connection,
            membership,
        )
        append_audit_event(
            database_connection,
            AuditEvent(
                event_type="cohort_enrolled",
                handle=enrollment_input.handle,
                source=enrollment_input.source,
                created_at=enrollment_input.joined_at,
                payload={
                    "course_id": enrollment_input.course_id,
                    "rank_eligible": enrollment_input.rank_eligible,
                },
            ),
        )
        enqueue_outbox_item(
            database_connection,
            projection_outbox_item(
                handle=enrollment_input.handle,
                course_id=enrollment_input.course_id,
                created_at=enrollment_input.joined_at,
                reason="enrollment",
            ),
        )
        return EnrollmentResult(membership=membership, created=True)
