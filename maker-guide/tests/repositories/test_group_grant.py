"""Tests for group grant repository functions."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from maker_guide.repositories.group_grant import (
    GroupGrant,
    GroupIntendedState,
    list_all_group_grants,
    list_group_grants,
    list_present_group_grants,
    upsert_group_grant,
)
from maker_guide.repositories.helpers import RepositoryError, connect_database
from maker_guide.repositories.learner import Learner, upsert_learner
from tests.repositories.helpers import TIMESTAMP, write_learner


def test_group_grant_upsert_reads_and_updates(migrated_database_path: Path) -> None:
    """Group grant state can be inserted, read, and updated idempotently."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        upsert_group_grant(database_connection, _group_grant(intended_state="present"))
        upsert_group_grant(database_connection, _group_grant(intended_state="absent"))

        assert list_group_grants(database_connection, "alice") == [
            _group_grant(intended_state="absent"),
        ]


def test_group_grants_list_all_and_present_only(migrated_database_path: Path) -> None:
    """Group sync can list every intended state and filter present memberships."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        upsert_learner(
            database_connection,
            Learner(
                handle="bob",
                joined_at=TIMESTAMP,
                tagline=None,
                created_at=TIMESTAMP,
            ),
        )
        upsert_group_grant(database_connection, _group_grant(intended_state="present"))
        upsert_group_grant(
            database_connection,
            GroupGrant(
                handle="bob",
                group_name="makers",
                intended_state="absent",
                reason="tier",
                updated_at=TIMESTAMP,
            ),
        )

        assert list_all_group_grants(database_connection) == [
            _group_grant(intended_state="present"),
            GroupGrant(
                handle="bob",
                group_name="makers",
                intended_state="absent",
                reason="tier",
                updated_at=TIMESTAMP,
            ),
        ]
        assert list_present_group_grants(database_connection) == [
            _group_grant(intended_state="present"),
        ]


@pytest.mark.parametrize(
    ("group_grant", "error_pattern"),
    [
        (
            GroupGrant(
                handle="bad handle",
                group_name="makers",
                intended_state="present",
                reason="tier",
                updated_at=TIMESTAMP,
            ),
            "handle must be a safe Unix name",
        ),
        (
            GroupGrant(
                handle="alice",
                group_name="bad group",
                intended_state="present",
                reason="tier",
                updated_at=TIMESTAMP,
            ),
            "group name must be a safe Unix name",
        ),
        (
            GroupGrant(
                handle="alice",
                group_name="makers",
                intended_state=cast("GroupIntendedState", "unknown"),
                reason="tier",
                updated_at=TIMESTAMP,
            ),
            "intended state must be present or absent",
        ),
    ],
)
def test_group_grant_rejects_unsafe_intent(
    migrated_database_path: Path,
    group_grant: GroupGrant,
    error_pattern: str,
) -> None:
    """Repository writes reject intent that cannot be safely projected."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)

        with pytest.raises(RepositoryError, match=error_pattern):
            upsert_group_grant(database_connection, group_grant)


def _group_grant(intended_state: GroupIntendedState) -> GroupGrant:
    return GroupGrant(
        handle="alice",
        group_name="makers",
        intended_state=intended_state,
        reason="tier",
        updated_at=TIMESTAMP,
    )
