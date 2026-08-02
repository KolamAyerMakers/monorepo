"""Validation path resolution for deterministic quest checks."""

from __future__ import annotations

import os
import pwd
import stat
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal

type ValidationPathFailureReason = Literal[
    "unknown-user",
    "unsafe-path",
    "path-escapes-scope",
    "missing-path",
    "broken-symlink",
    "symlink-loop",
    "permission-denied",
    "read-error",
]
type ValidationFileOpenFailureReason = ValidationPathFailureReason | Literal["not-regular-file"]
_SYMLINK_RESOLUTION_LIMIT = 40


@dataclass(frozen=True, kw_only=True, slots=True)
class UnixAccount:
    """Unix account data needed for validation path resolution."""

    handle: str
    """Learner handle matching the Unix account name."""
    user_id: int
    """Unix user id."""
    home_directory: Path
    """Unix home directory for the learner."""


@dataclass(frozen=True, kw_only=True, slots=True)
class ValidationPathResolution:
    """Resolved catalog validation path or stable failure reason."""

    catalog_path: str
    """Catalog-declared validation path."""
    candidate_path: Path | None
    """Path after applying learner-home expansion."""
    target_path: Path | None
    """Resolved path after following symlinks."""
    home_path: Path | None
    """Learner home directory from the Unix account, when it exists."""
    failure_reason: ValidationPathFailureReason | None
    """Stable reason when resolution fails."""


@dataclass(frozen=True, kw_only=True, slots=True)
class ValidationFileOpen:
    """Validation path result with an opened file descriptor."""

    resolution: ValidationPathResolution
    """Path resolution metadata for validation evidence."""
    file_descriptor: int | None
    """Opened descriptor, owned by the caller when present."""
    failure_reason: ValidationFileOpenFailureReason | None
    """Stable reason when opening or descriptor validation fails."""


type UnixAccountLookup = Callable[[str], UnixAccount | None]


def lookup_unix_account(handle: str) -> UnixAccount | None:
    """Return Unix account data for a learner handle."""
    try:
        user_record = pwd.getpwnam(handle)
    except KeyError:
        return None
    return UnixAccount(
        handle=handle,
        user_id=user_record.pw_uid,
        home_directory=Path(user_record.pw_dir),
    )


def resolve_validation_path(
    handle: str,
    catalog_path: str,
    *,
    account_lookup: UnixAccountLookup = lookup_unix_account,
) -> ValidationPathResolution:
    """Resolve one active catalog validation path without reading or executing it."""
    unix_account = account_lookup(handle)
    if unix_account is None:
        return _failed_resolution(catalog_path, None, None, "unknown-user")
    return _resolve_validation_path_for_account(unix_account, catalog_path)


def open_validation_file(
    handle: str,
    catalog_path: str,
    *,
    account_lookup: UnixAccountLookup = lookup_unix_account,
) -> ValidationFileOpen:
    """Open one catalog validation file and validate the opened descriptor."""
    resolution = resolve_validation_path(handle, catalog_path, account_lookup=account_lookup)
    if resolution.failure_reason is not None:
        return ValidationFileOpen(
            resolution=resolution,
            file_descriptor=None,
            failure_reason=resolution.failure_reason,
        )
    if resolution.candidate_path is None or resolution.home_path is None:
        return ValidationFileOpen(
            resolution=resolution,
            file_descriptor=None,
            failure_reason="read-error",
        )
    return _open_resolved_validation_file(resolution)


def _resolve_validation_path_for_account(
    unix_account: UnixAccount,
    catalog_path: str,
) -> ValidationPathResolution:
    home_path = unix_account.home_directory
    if _unsafe_catalog_path(catalog_path):
        return _failed_resolution(catalog_path, None, home_path, "unsafe-path")

    candidate_path = _candidate_path(home_path, catalog_path)
    if candidate_path is None:
        return _failed_resolution(catalog_path, None, home_path, "unsafe-path")

    resolution = _resolve_filesystem_target(catalog_path, candidate_path, home_path)
    if resolution.failure_reason is not None:
        return resolution
    if resolution.target_path is None:
        return _failed_resolution(catalog_path, candidate_path, home_path, "read-error")

    if scope_failure := _validate_learner_home_scope(
        catalog_path,
        candidate_path,
        home_path,
        resolution.target_path,
    ):
        return scope_failure
    return resolution


def _open_resolved_validation_file(resolution: ValidationPathResolution) -> ValidationFileOpen:
    if resolution.candidate_path is None or resolution.home_path is None:
        return ValidationFileOpen(
            resolution=resolution,
            file_descriptor=None,
            failure_reason="read-error",
        )
    try:
        file_descriptor = os.open(
            resolution.candidate_path,
            os.O_RDONLY | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0),
        )
    except FileNotFoundError:
        return ValidationFileOpen(
            resolution=resolution,
            file_descriptor=None,
            failure_reason=_missing_target_failure_reason(resolution.candidate_path),
        )
    except PermissionError:
        return ValidationFileOpen(
            resolution=resolution,
            file_descriptor=None,
            failure_reason="permission-denied",
        )
    except OSError:
        return ValidationFileOpen(
            resolution=resolution,
            file_descriptor=None,
            failure_reason="read-error",
        )
    try:
        return _validate_open_validation_file_descriptor(resolution, file_descriptor)
    except BaseException:
        os.close(file_descriptor)
        raise


def _validate_open_validation_file_descriptor(
    resolution: ValidationPathResolution,
    file_descriptor: int,
) -> ValidationFileOpen:
    if failure_reason := _open_file_descriptor_failure_reason(file_descriptor):
        os.close(file_descriptor)
        return _failed_file_open(resolution, failure_reason)

    target_result = _open_file_descriptor_target_path(file_descriptor)
    if isinstance(target_result, str):
        os.close(file_descriptor)
        return _failed_file_open(resolution, target_result)

    if resolution.candidate_path is None or resolution.home_path is None:
        os.close(file_descriptor)
        return _failed_file_open(resolution, "read-error")
    if scope_failure := _validate_learner_home_scope(
        resolution.catalog_path,
        resolution.candidate_path,
        resolution.home_path,
        target_result,
    ):
        os.close(file_descriptor)
        return _failed_file_open(scope_failure, scope_failure.failure_reason or "read-error")
    return ValidationFileOpen(
        resolution=ValidationPathResolution(
            catalog_path=resolution.catalog_path,
            candidate_path=resolution.candidate_path,
            target_path=target_result,
            home_path=resolution.home_path,
            failure_reason=None,
        ),
        file_descriptor=file_descriptor,
        failure_reason=None,
    )


def _open_file_descriptor_failure_reason(
    file_descriptor: int,
) -> ValidationFileOpenFailureReason | None:
    try:
        file_status = os.fstat(file_descriptor)
    except OSError:
        return "read-error"
    if not stat.S_ISREG(file_status.st_mode):
        return "not-regular-file"
    return None


def _open_file_descriptor_target_path(
    file_descriptor: int,
) -> Path | ValidationFileOpenFailureReason:
    try:
        return Path(f"/proc/self/fd/{file_descriptor}").resolve(strict=True)
    except PermissionError:
        return "permission-denied"
    except OSError:
        return "read-error"


def _failed_file_open(
    resolution: ValidationPathResolution,
    failure_reason: ValidationFileOpenFailureReason,
) -> ValidationFileOpen:
    return ValidationFileOpen(
        resolution=resolution,
        file_descriptor=None,
        failure_reason=failure_reason,
    )


def _resolve_filesystem_target(
    catalog_path: str,
    candidate_path: Path,
    home_path: Path,
) -> ValidationPathResolution:
    failure_reason: ValidationPathFailureReason
    try:
        target_path = candidate_path.resolve(strict=True)
    except FileNotFoundError:
        failure_reason = _missing_target_failure_reason(candidate_path)
    except RuntimeError:
        failure_reason = "symlink-loop"
    except PermissionError:
        failure_reason = "permission-denied"
    except OSError:
        failure_reason = _symlink_failure_reason(candidate_path) or "read-error"
    else:
        return ValidationPathResolution(
            catalog_path=catalog_path,
            candidate_path=candidate_path,
            target_path=target_path,
            home_path=home_path,
            failure_reason=None,
        )
    return _failed_resolution(catalog_path, candidate_path, home_path, failure_reason)


def _validate_learner_home_scope(
    catalog_path: str,
    candidate_path: Path,
    home_path: Path,
    target_path: Path,
) -> ValidationPathResolution | None:
    if not _requires_home_scope(catalog_path):
        return None
    if home_resolution_failure := _home_resolution_failure(catalog_path, candidate_path, home_path):
        return home_resolution_failure
    if _is_relative_to(target_path, home_path.resolve(strict=True)):
        return None
    return _failed_resolution(
        catalog_path,
        candidate_path,
        home_path,
        "path-escapes-scope",
        target_path=target_path,
    )


def _home_resolution_failure(
    catalog_path: str,
    candidate_path: Path,
    home_path: Path,
) -> ValidationPathResolution | None:
    failure_reason: ValidationPathFailureReason
    try:
        home_path.resolve(strict=True)
    except FileNotFoundError:
        failure_reason = "missing-path"
    except RuntimeError:
        failure_reason = "symlink-loop"
    except PermissionError:
        failure_reason = "permission-denied"
    except OSError:
        failure_reason = "read-error"
    else:
        return None
    return _failed_resolution(catalog_path, candidate_path, home_path, failure_reason)


def _failed_resolution(
    catalog_path: str,
    candidate_path: Path | None,
    home_path: Path | None,
    failure_reason: ValidationPathFailureReason,
    *,
    target_path: Path | None = None,
) -> ValidationPathResolution:
    return ValidationPathResolution(
        catalog_path=catalog_path,
        candidate_path=candidate_path,
        target_path=target_path,
        home_path=home_path,
        failure_reason=failure_reason,
    )


def _unsafe_catalog_path(catalog_path: str) -> bool:
    if catalog_path.strip() == "" or "\\" in catalog_path:
        return True
    return any(path_part in {".", ".."} for path_part in catalog_path.split("/"))


def _missing_target_failure_reason(candidate_path: Path) -> ValidationPathFailureReason:
    return _symlink_failure_reason(candidate_path) or "missing-path"


def _symlink_failure_reason(candidate_path: Path) -> ValidationPathFailureReason | None:
    if not candidate_path.is_symlink():
        return None
    if _symlink_loop_detected(candidate_path):
        return "symlink-loop"
    return "broken-symlink"


def _symlink_loop_detected(candidate_path: Path) -> bool:
    seen_paths: set[Path] = set()
    current_path = candidate_path
    links_followed = 0
    while links_followed < _SYMLINK_RESOLUTION_LIMIT:
        if not current_path.is_symlink():
            return False
        absolute_current_path = current_path.absolute()
        if absolute_current_path in seen_paths:
            return True
        seen_paths.add(absolute_current_path)
        try:
            target_path = current_path.readlink()
        except OSError:
            return False
        current_path = (
            target_path if target_path.is_absolute() else current_path.parent / target_path
        )
        links_followed += 1
    return True


def _candidate_path(home_path: Path, catalog_path: str) -> Path | None:
    if catalog_path == "~":
        return home_path
    if catalog_path.startswith("~/"):
        return home_path / catalog_path.removeprefix("~/")
    if catalog_path.startswith("~"):
        return None
    if PurePosixPath(catalog_path).is_absolute():
        return Path(catalog_path)
    return home_path / catalog_path


def _requires_home_scope(catalog_path: str) -> bool:
    return not PurePosixPath(catalog_path).is_absolute()


def _is_relative_to(path: Path, parent_path: Path) -> bool:
    return path == parent_path or parent_path in path.parents
