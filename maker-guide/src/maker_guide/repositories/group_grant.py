"""Group grant repository functions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Literal, cast

from maker_guide.repositories.helpers import RepositoryError
from maker_guide.unix_names import is_safe_unix_name

GroupIntendedState = Literal["present", "absent"]


@dataclass(frozen=True, kw_only=True, slots=True)
class GroupGrant:
    """Intended Unix group state for a learner."""

    handle: str
    """Shared learner id."""
    group_name: str
    """Unix group name."""
    intended_state: GroupIntendedState
    """Desired group membership state."""
    reason: str
    """Reason this group state is intended."""
    updated_at: str
    """ISO timestamp for when intended state changed."""


def upsert_group_grant(database_connection: sqlite3.Connection, grant: GroupGrant) -> None:
    """Insert or update intended group state."""
    _validate_group_grant(grant)
    database_connection.execute(
        """
        insert into group_grants (handle, group_name, intended_state, reason, updated_at)
        values (?, ?, ?, ?, ?)
        on conflict(handle, group_name) do update set
            intended_state = excluded.intended_state,
            reason = excluded.reason,
            updated_at = excluded.updated_at
        """,
        (grant.handle, grant.group_name, grant.intended_state, grant.reason, grant.updated_at),
    )


def list_group_grants(database_connection: sqlite3.Connection, handle: str) -> list[GroupGrant]:
    """Return intended group state for a learner."""
    grant_records = cast(
        "list[tuple[str, str, str, str, str]]",
        database_connection.execute(
            """
            select handle, group_name, intended_state, reason, updated_at
            from group_grants
            where handle = ?
            order by group_name
            """,
            (handle,),
        ).fetchall(),
    )
    return [_group_grant_from_record(grant_record) for grant_record in grant_records]


def list_all_group_grants(database_connection: sqlite3.Connection) -> list[GroupGrant]:
    """Return all intended group states in deterministic order."""
    grant_records = cast(
        "list[tuple[str, str, str, str, str]]",
        database_connection.execute(
            """
            select handle, group_name, intended_state, reason, updated_at
            from group_grants
            order by group_name, handle
            """,
        ).fetchall(),
    )
    return [_group_grant_from_record(grant_record) for grant_record in grant_records]


def list_present_group_grants(database_connection: sqlite3.Connection) -> list[GroupGrant]:
    """Return intended present group memberships in deterministic order."""
    grant_records = cast(
        "list[tuple[str, str, str, str, str]]",
        database_connection.execute(
            """
            select handle, group_name, intended_state, reason, updated_at
            from group_grants
            where intended_state = 'present'
            order by group_name, handle
            """,
        ).fetchall(),
    )
    return [_group_grant_from_record(grant_record) for grant_record in grant_records]


def _group_grant_from_record(grant_record: tuple[str, str, str, str, str]) -> GroupGrant:
    if grant_record[2] not in {"present", "absent"}:
        raise RepositoryError("group grant intended state must be present or absent")
    group_grant = GroupGrant(
        handle=grant_record[0],
        group_name=grant_record[1],
        intended_state=cast("GroupIntendedState", grant_record[2]),
        reason=grant_record[3],
        updated_at=grant_record[4],
    )
    _validate_group_grant(group_grant)
    return group_grant


def _validate_group_grant(group_grant: GroupGrant) -> None:
    if not is_safe_unix_name(group_grant.handle):
        raise RepositoryError("group grant handle must be a safe Unix name")
    if not is_safe_unix_name(group_grant.group_name):
        raise RepositoryError("group grant group name must be a safe Unix name")
    if group_grant.intended_state not in {"present", "absent"}:
        raise RepositoryError("group grant intended state must be present or absent")
    if not group_grant.reason:
        raise RepositoryError("group grant reason must be non-empty")
    if not group_grant.updated_at:
        raise RepositoryError("group grant updated_at must be non-empty")
