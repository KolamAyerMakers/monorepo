"""Restricted full LLM audit log repository functions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import cast

from maker_guide.repositories.helpers import JsonPayload, dump_json, last_inserted_id, load_json


@dataclass(frozen=True, kw_only=True, slots=True)
class LlmAuditLog:
    """One restricted full request/response audit row for LLM tutor use."""

    id: int | None = None
    """SQLite-generated audit id, absent before insert."""
    handle: str
    """Shared learner id."""
    course_id: str
    """Course id from the Python curriculum catalog."""
    source: str
    """Chat source that requested the tutor."""
    created_at: str
    """ISO timestamp for when the LLM interaction was attempted."""
    provider: str
    """LLM provider id, or unavailable when no provider response was reached."""
    model: str
    """LLM model id, or unavailable when no provider response was reached."""
    status: str
    """Interaction status, such as answered, failed, or rate_limited."""
    request: JsonPayload
    """Full provider request payload, without API credentials."""
    response: JsonPayload
    """Full provider response payload or structured failure details."""
    expires_at: str
    """ISO timestamp after which this restricted audit row may be pruned."""


def append_llm_audit_log(database_connection: sqlite3.Connection, audit_log: LlmAuditLog) -> int:
    """Append a restricted LLM audit log and return its id."""
    return last_inserted_id(
        database_connection.execute(
            """
            insert into llm_audit_logs
                (handle, course_id, source, created_at, provider, model, status,
                request_json, response_json, expires_at)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                audit_log.handle,
                audit_log.course_id,
                audit_log.source,
                audit_log.created_at,
                audit_log.provider,
                audit_log.model,
                audit_log.status,
                dump_json(audit_log.request),
                dump_json(audit_log.response),
                audit_log.expires_at,
            ),
        ),
    )


def list_llm_audit_logs(
    database_connection: sqlite3.Connection,
    handle: str,
    limit: int,
) -> list[LlmAuditLog]:
    """Return restricted LLM audit logs for one learner in newest-first order."""
    audit_log_records = cast(
        "list[tuple[int, str, str, str, str, str, str, str, str, str, str]]",
        database_connection.execute(
            """
            select id, handle, course_id, source, created_at, provider, model, status,
                request_json, response_json, expires_at
            from llm_audit_logs
            where handle = ?
            order by id desc
            limit ?
            """,
            (handle, limit),
        ).fetchall(),
    )
    return [_llm_audit_log_from_record(audit_log_record) for audit_log_record in audit_log_records]


def count_llm_audit_logs(database_connection: sqlite3.Connection) -> int:
    """Return the number of restricted LLM audit rows."""
    return cast(
        "tuple[int]",
        database_connection.execute("select count(*) from llm_audit_logs").fetchone(),
    )[0]


def delete_llm_audit_logs_expired_before(
    database_connection: sqlite3.Connection,
    expires_before: str,
) -> int:
    """Delete restricted LLM audit rows whose expiry timestamp has passed."""
    cursor = database_connection.execute(
        "delete from llm_audit_logs where expires_at < ?",
        (expires_before,),
    )
    return cursor.rowcount


def _llm_audit_log_from_record(
    audit_log_record: tuple[int, str, str, str, str, str, str, str, str, str, str],
) -> LlmAuditLog:
    return LlmAuditLog(
        id=audit_log_record[0],
        handle=audit_log_record[1],
        course_id=audit_log_record[2],
        source=audit_log_record[3],
        created_at=audit_log_record[4],
        provider=audit_log_record[5],
        model=audit_log_record[6],
        status=audit_log_record[7],
        request=load_json(audit_log_record[8]),
        response=load_json(audit_log_record[9]),
        expires_at=audit_log_record[10],
    )
