"""Export committed audit rows to JSON Lines."""

from __future__ import annotations

import fcntl
import json
import os
import sqlite3
import stat
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO, cast
from zoneinfo import ZoneInfo

from maker_guide.repositories.audit_event import (
    AuditEvent,
    list_unexported_audit_events,
    mark_audit_event_exported,
)

_LOCK_FILENAME = ".export.lock"
_AUDIT_DIRECTORY_MODE = 0o700
_AUDIT_FILE_MODE = 0o600


class AuditExportError(RuntimeError):
    """Raised when committed audit rows cannot be exported."""


@dataclass(frozen=True, kw_only=True, slots=True)
class AuditExportOptions:
    """Options for one audit export pass."""

    audit_root: Path
    """Directory containing date-partitioned JSONL files."""
    exported_at: str
    """Timestamp written to exported audit rows after append succeeds."""
    timezone: str
    """Timezone used to select date-partitioned JSONL files."""
    limit: int = 1000
    """Maximum number of unexported audit rows to process."""


@dataclass(frozen=True, kw_only=True, slots=True)
class AuditExportResult:
    """Result of one audit export pass."""

    exported_count: int
    """Number of audit rows appended and marked exported."""
    audit_root: Path
    """Directory containing date-partitioned JSONL files."""


def export_audit_events(
    database_connection: sqlite3.Connection,
    options: AuditExportOptions,
) -> AuditExportResult:
    """Append unexported audit rows to JSONL and mark rows after successful append."""
    exported_count = 0
    _ensure_audit_directory(options.audit_root)
    _fsync_directory(options.audit_root)
    with _audit_export_lock(options.audit_root):
        for audit_event in list_unexported_audit_events(database_connection, options.limit):
            _append_audit_event(options.audit_root, options.timezone, audit_event)
            if audit_event.id is None:
                raise AuditExportError("audit event has no id")
            with database_connection:
                mark_audit_event_exported(
                    database_connection,
                    audit_event.id,
                    options.exported_at,
                )
            exported_count += 1
    return AuditExportResult(exported_count=exported_count, audit_root=options.audit_root)


@contextmanager
def _audit_export_lock(audit_root: Path) -> Generator[None]:
    lock_path = audit_root / _LOCK_FILENAME
    with _open_audit_file(lock_path, "a+") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise AuditExportError(
                f"audit export already in progress for {audit_root}",
            ) from error
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _append_audit_event(audit_root: Path, timezone: str, audit_event: AuditEvent) -> None:
    if audit_event.id is None:
        raise AuditExportError("audit event has no id")
    with _open_audit_file(
        _partition_path(audit_root, timezone, audit_event.created_at),
        "a",
    ) as file_object:
        file_object.write(f"{json.dumps(_jsonl_payload(audit_event), sort_keys=True)}\n")
        file_object.flush()
        os.fsync(file_object.fileno())
    _fsync_directory(audit_root)


def _ensure_audit_directory(audit_root: Path) -> None:
    if audit_root.is_symlink():
        raise AuditExportError(f"unsafe symlinked audit directory: {audit_root}")
    audit_root.mkdir(mode=_AUDIT_DIRECTORY_MODE, parents=True, exist_ok=True)
    if not audit_root.is_dir() or audit_root.is_symlink():
        raise AuditExportError(f"unsafe audit directory: {audit_root}")
    audit_root.chmod(_AUDIT_DIRECTORY_MODE)


@contextmanager
def _open_audit_file(path: Path, mode: str) -> Generator[TextIO]:
    flags = os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW
    if "a" in mode:
        flags |= os.O_APPEND
    if "+" in mode:
        flags |= os.O_RDWR
    else:
        flags |= os.O_WRONLY
    try:
        file_descriptor = os.open(path, flags, _AUDIT_FILE_MODE)
    except OSError as error:
        raise AuditExportError(f"unsafe audit export path: {path}") from error
    try:
        _validate_audit_file_descriptor(path, file_descriptor)
        with os.fdopen(file_descriptor, mode, encoding="utf-8") as file_object:
            file_descriptor = -1
            yield cast("TextIO", file_object)
    finally:
        if file_descriptor >= 0:
            os.close(file_descriptor)


def _validate_audit_file_descriptor(path: Path, file_descriptor: int) -> None:
    try:
        file_status = os.fstat(file_descriptor)
    except OSError as error:
        raise AuditExportError(f"could not inspect audit export path: {path}") from error
    if not stat.S_ISREG(file_status.st_mode):
        raise AuditExportError(f"audit export path is not a regular file: {path}")
    os.fchmod(file_descriptor, _AUDIT_FILE_MODE)


def _fsync_directory(directory: Path) -> None:
    directory_file_descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_file_descriptor)
    finally:
        os.close(directory_file_descriptor)


def _partition_path(audit_root: Path, timezone: str, created_at: str) -> Path:
    return audit_root / f"{_created_date(created_at, timezone)}.jsonl"


def _created_date(created_at: str, timezone: str) -> str:
    return _parse_timestamp(created_at).astimezone(ZoneInfo(timezone)).date().isoformat()


def _parse_timestamp(timestamp: str) -> datetime:
    normalized_timestamp = (
        timestamp.removesuffix("Z") + "+00:00" if timestamp.endswith("Z") else timestamp
    )
    parsed_timestamp = datetime.fromisoformat(normalized_timestamp)
    if parsed_timestamp.tzinfo is None:
        return parsed_timestamp.replace(tzinfo=UTC)
    return parsed_timestamp.astimezone(UTC)


def _jsonl_payload(audit_event: AuditEvent) -> dict[str, object]:
    if audit_event.id is None:
        raise AuditExportError("audit event has no id")
    return {
        "audit_id": audit_event.id,
        "created_at": audit_event.created_at,
        "event_type": audit_event.event_type,
        "handle": audit_event.handle,
        "payload": audit_event.payload,
        "source": audit_event.source,
    }
