"""Narrow privileged helpers for Unix group mutation."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from maker_guide.config import DEFAULT_CONFIG_PATH, ConfigError, load_unix_groups_config
from maker_guide.unix_names import is_safe_unix_name

USERMOD_COMMAND = Path("/usr/sbin/usermod")
GPASSWD_COMMAND = Path("/usr/bin/gpasswd")
SYSTEM_COMMAND_TIMEOUT_SECONDS = 10.0
SYSTEM_COMMAND_TIMEOUT_RETURN_CODE = 124

type SystemCommandRunner = Callable[[Sequence[str]], int]


class UnixGroupHelperError(ValueError):
    """Raised when helper arguments are invalid."""


def run_grant_group_helper(
    arguments: Sequence[str],
    command_runner: SystemCommandRunner | None = None,
    managed_groups: frozenset[str] | None = None,
) -> int:
    """Grant one user to one group with a fixed system command."""
    handle, group_name = _validated_helper_arguments(arguments)
    _require_managed_group(group_name, managed_groups)
    return (command_runner or _run_system_command)(
        (str(USERMOD_COMMAND), "-a", "-G", group_name, handle),
    )


def run_revoke_group_helper(
    arguments: Sequence[str],
    command_runner: SystemCommandRunner | None = None,
    managed_groups: frozenset[str] | None = None,
) -> int:
    """Remove one user from one group with a fixed system command."""
    handle, group_name = _validated_helper_arguments(arguments)
    _require_managed_group(group_name, managed_groups)
    return (command_runner or _run_system_command)(
        (str(GPASSWD_COMMAND), "-d", handle, group_name),
    )


def main_grant_group() -> None:
    """Console entrypoint for the grant helper."""
    raise SystemExit(
        _run_helper_entrypoint(
            _grant_group_helper_from_default_config,
            sys.argv[1:],
        ),
    )


def main_revoke_group() -> None:
    """Console entrypoint for the revoke helper."""
    raise SystemExit(
        _run_helper_entrypoint(
            _revoke_group_helper_from_default_config,
            sys.argv[1:],
        ),
    )


def _run_helper_entrypoint(
    helper: Callable[[Sequence[str]], int],
    arguments: Sequence[str],
) -> int:
    try:
        return helper(arguments)
    except UnixGroupHelperError as helper_error:
        sys.stderr.write(f"{helper_error}\n")
        return 2
    except subprocess.TimeoutExpired as timeout_error:
        sys.stderr.write(f"system command timed out after {timeout_error.timeout:g} seconds\n")
        return SYSTEM_COMMAND_TIMEOUT_RETURN_CODE


def _validated_helper_arguments(arguments: Sequence[str]) -> tuple[str, str]:
    if len(arguments) != 2:
        raise UnixGroupHelperError("expected exactly: handle group_name")
    handle, group_name = arguments
    if not is_safe_unix_name(handle):
        raise UnixGroupHelperError("handle must be a safe Unix name")
    if not is_safe_unix_name(group_name):
        raise UnixGroupHelperError("group_name must be a safe Unix name")
    return handle, group_name


def _grant_group_helper_from_default_config(arguments: Sequence[str]) -> int:
    return run_grant_group_helper(
        arguments,
        managed_groups=_managed_groups_from_default_config(),
    )


def _revoke_group_helper_from_default_config(arguments: Sequence[str]) -> int:
    return run_revoke_group_helper(
        arguments,
        managed_groups=_managed_groups_from_default_config(),
    )


def _managed_groups_from_default_config() -> frozenset[str]:
    try:
        unix_groups_configuration = load_unix_groups_config(DEFAULT_CONFIG_PATH)
    except (ConfigError, OSError) as error:
        raise UnixGroupHelperError(
            f"could not load managed groups from {DEFAULT_CONFIG_PATH}",
        ) from error
    if unix_groups_configuration is None:
        raise UnixGroupHelperError("unix group helper requires enabled unix_groups config")
    return unix_groups_configuration.managed_groups


def _require_managed_group(group_name: str, managed_groups: frozenset[str] | None) -> None:
    if not managed_groups:
        raise UnixGroupHelperError("managed groups are required")
    if group_name not in managed_groups:
        raise UnixGroupHelperError(f"unmanaged group: {group_name}")


def _run_system_command(arguments: Sequence[str]) -> int:
    return subprocess.run(  # noqa: S603
        list(arguments),
        check=False,
        timeout=SYSTEM_COMMAND_TIMEOUT_SECONDS,
    ).returncode
