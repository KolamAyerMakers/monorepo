"""Validation helpers for Unix account and group names."""

from __future__ import annotations

import re

_UNIX_NAME_PATTERN = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")
_FORBIDDEN_MANAGED_GROUPS = frozenset({"adm", "docker", "root", "sudo", "wheel"})


def is_safe_unix_name(name: str) -> bool:
    """Return whether a value is safe to pass to Unix account commands."""
    return _UNIX_NAME_PATTERN.fullmatch(name) is not None


def is_allowed_managed_group_name(name: str) -> bool:
    """Return whether a Unix group can be managed by maker-guide."""
    return is_safe_unix_name(name) and name not in _FORBIDDEN_MANAGED_GROUPS
