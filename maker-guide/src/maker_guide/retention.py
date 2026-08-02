"""Retention cleanup for raw learner evidence."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from maker_guide.curriculum.models import CourseCatalog
from maker_guide.repositories.command_observation import delete_command_observations_before
from maker_guide.repositories.helpers import transaction
from maker_guide.repositories.llm_audit_log import delete_llm_audit_logs_expired_before

LLM_AUDIT_RETENTION_DAYS = 90


@dataclass(frozen=True, kw_only=True, slots=True)
class ObservationRetentionResult:
    """Result of command observation retention cleanup."""

    cleanup_due: bool
    """Whether the retention window has expired."""
    cutoff_at: str
    """UTC timestamp before which raw observations may be pruned."""
    deleted_count: int
    """Number of raw command observations deleted."""


@dataclass(frozen=True, kw_only=True, slots=True)
class LlmAuditRetentionResult:
    """Result of restricted LLM audit retention cleanup."""

    cutoff_at: str
    """UTC timestamp before which expired LLM audit rows were pruned."""
    deleted_count: int
    """Number of restricted LLM audit rows deleted."""


def prune_command_observations(
    database_connection: sqlite3.Connection,
    catalog: CourseCatalog,
    today: date,
) -> ObservationRetentionResult:
    """Delete raw command observations after the course retention window expires."""
    cutoff_date = catalog.course.ends_on + timedelta(days=30)
    cutoff_at = f"{cutoff_date.isoformat()}T00:00:00Z"
    if today <= cutoff_date:
        return ObservationRetentionResult(
            cleanup_due=False,
            cutoff_at=cutoff_at,
            deleted_count=0,
        )
    with transaction(database_connection):
        return ObservationRetentionResult(
            cleanup_due=True,
            cutoff_at=cutoff_at,
            deleted_count=delete_command_observations_before(
                database_connection,
                catalog.course.id,
                cutoff_at,
            ),
        )


def llm_audit_expires_at(created_at: str) -> str:
    """Return the restricted LLM audit expiry timestamp for a creation timestamp."""
    return _format_utc_timestamp(
        _parse_utc_timestamp(created_at) + timedelta(days=LLM_AUDIT_RETENTION_DAYS),
    )


def prune_llm_audit_logs(
    database_connection: sqlite3.Connection,
    now: str,
) -> LlmAuditRetentionResult:
    """Delete restricted full LLM audit logs after their explicit expiry timestamp."""
    with transaction(database_connection):
        return LlmAuditRetentionResult(
            cutoff_at=now,
            deleted_count=delete_llm_audit_logs_expired_before(database_connection, now),
        )


def _parse_utc_timestamp(timestamp: str) -> datetime:
    parsed_timestamp = datetime.fromisoformat(timestamp)
    if parsed_timestamp.tzinfo is None:
        return parsed_timestamp.replace(tzinfo=UTC)
    return parsed_timestamp.astimezone(UTC)


def _format_utc_timestamp(timestamp: datetime) -> str:
    return timestamp.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
