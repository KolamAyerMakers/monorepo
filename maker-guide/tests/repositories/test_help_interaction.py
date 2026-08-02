"""Tests for help interaction repository functions."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from maker_guide.repositories.help_interaction import (
    HelpInteraction,
    add_help_interaction,
    answer_help_interaction,
    get_help_interaction,
    list_recent_help_interactions,
)
from maker_guide.repositories.helpers import connect_database
from tests.repositories.helpers import TIMESTAMP, write_learner


def test_help_interaction_round_trips_topics_and_answer(migrated_database_path: Path) -> None:
    """Help interactions preserve topic tags and can be answered."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        interaction_id = add_help_interaction(database_connection, _interaction())
        answer_help_interaction(
            database_connection,
            interaction_id,
            "try man ls",
            "2026-07-11T09:01:00Z",
        )

        assert get_help_interaction(database_connection, interaction_id) == HelpInteraction(
            id=interaction_id,
            handle="alice",
            source="cli",
            visibility="private",
            question="what now?",
            response="try man ls",
            topic_tags=("navigation", "ls"),
            created_at=TIMESTAMP,
            answered_at="2026-07-11T09:01:00Z",
        )


def test_help_interaction_lists_recent_rows(migrated_database_path: Path) -> None:
    """Recent help interactions are returned newest first for snapshots."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        add_help_interaction(database_connection, _interaction())
        latest_interaction_id = add_help_interaction(
            database_connection,
            HelpInteraction(
                id=None,
                handle="alice",
                source="irc",
                visibility="public",
                question="grep help",
                response="try man grep",
                topic_tags=("grep",),
                created_at="2026-07-11T09:02:00Z",
                answered_at="2026-07-11T09:02:00Z",
            ),
        )

        assert [
            interaction.id
            for interaction in list_recent_help_interactions(database_connection, "alice", 1)
        ] == [latest_interaction_id]


def test_help_interaction_filters_recent_rows_by_source_and_visibility(
    migrated_database_path: Path,
) -> None:
    """Context history excludes interactions from other transports and visibility levels."""
    with connect_database(migrated_database_path) as database_connection:
        write_learner(database_connection)
        for index in range(5):
            add_help_interaction(
                database_connection,
                HelpInteraction(
                    id=None,
                    handle="alice",
                    source="cli",
                    visibility="private",
                    question=f"cli {index}",
                    response=f"answer {index}",
                    topic_tags=(),
                    created_at=f"2026-07-11T09:0{index}:00Z",
                    answered_at=f"2026-07-11T09:0{index}:00Z",
                ),
            )
        add_help_interaction(
            database_connection,
            HelpInteraction(
                id=None,
                handle="alice",
                source="irc",
                visibility="private",
                question="irc private",
                response="exclude transport",
                topic_tags=(),
                created_at="2026-07-11T09:06:00Z",
                answered_at="2026-07-11T09:06:00Z",
            ),
        )
        add_help_interaction(
            database_connection,
            HelpInteraction(
                id=None,
                handle="alice",
                source="cli",
                visibility="public",
                question="cli public",
                response="exclude visibility",
                topic_tags=(),
                created_at="2026-07-11T09:07:00Z",
                answered_at="2026-07-11T09:07:00Z",
            ),
        )

        assert [
            interaction.question
            for interaction in list_recent_help_interactions(
                database_connection,
                "alice",
                4,
                source="cli",
                visibility="private",
            )
        ] == ["cli 4", "cli 3", "cli 2", "cli 1"]


def test_help_interaction_requires_known_learner(migrated_database_path: Path) -> None:
    """The schema rejects anonymous help interactions."""
    with (
        connect_database(migrated_database_path) as database_connection,
        pytest.raises(
            sqlite3.IntegrityError,
            match="NOT NULL constraint failed",
        ),
    ):
        database_connection.execute(
            """
            insert into help_interactions
                (handle, source, visibility, question, response, topic_tags,
                created_at, answered_at)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (None, "cli", "private", "hello", None, '{"tags":[]}', TIMESTAMP, None),
        )


def _interaction() -> HelpInteraction:
    return HelpInteraction(
        id=None,
        handle="alice",
        source="cli",
        visibility="private",
        question="what now?",
        response=None,
        topic_tags=("navigation", "ls"),
        created_at=TIMESTAMP,
        answered_at=None,
    )
