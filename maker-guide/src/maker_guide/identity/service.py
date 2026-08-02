"""Identity service flows."""

from __future__ import annotations

import sqlite3

from maker_guide.identity.models import EnsureLearnerInput, EnsureLearnerResult
from maker_guide.repositories.audit_event import AuditEvent, append_audit_event
from maker_guide.repositories.helpers import transaction
from maker_guide.repositories.learner import Learner, get_learner, upsert_learner
from maker_guide.repositories.outbox_item import enqueue_outbox_item, projection_outbox_item


def ensure_learner(
    database_connection: sqlite3.Connection,
    learner_input: EnsureLearnerInput,
) -> EnsureLearnerResult:
    """Create a learner identity if it does not already exist."""
    with transaction(database_connection):
        existing_learner = get_learner(database_connection, learner_input.handle)
        if existing_learner is not None:
            return EnsureLearnerResult(learner=existing_learner, created=False)

        learner = Learner(
            handle=learner_input.handle,
            joined_at=learner_input.joined_at,
            tagline=learner_input.tagline,
            created_at=learner_input.joined_at,
            uid=learner_input.uid,
        )
        upsert_learner(
            database_connection,
            learner,
        )
        append_audit_event(
            database_connection,
            AuditEvent(
                event_type="learner_created",
                handle=learner_input.handle,
                source=learner_input.source,
                created_at=learner_input.joined_at,
                payload={"handle": learner_input.handle},
            ),
        )
        enqueue_outbox_item(
            database_connection,
            projection_outbox_item(
                handle=learner_input.handle,
                created_at=learner_input.joined_at,
                reason="learner_created",
            ),
        )
        return EnsureLearnerResult(learner=learner, created=True)
