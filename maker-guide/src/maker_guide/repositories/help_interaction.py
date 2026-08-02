"""Help interaction repository functions."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import cast

from maker_guide.repositories.helpers import dump_json, last_inserted_id, topic_tags_from_json


@dataclass(frozen=True, kw_only=True, slots=True)
class HelpInteraction:
    """One learner help interaction."""

    id: int | None
    """SQLite-generated interaction id, absent before insert."""
    handle: str
    """Shared learner id."""
    source: str
    """Transport or subsystem that created the interaction."""
    visibility: str
    """Visibility of the interaction, public or private."""
    question: str
    """Learner question or request text."""
    response: str | None
    """Bot response text, if answered."""
    topic_tags: tuple[str, ...]
    """Derived topic labels for reporting and context."""
    created_at: str
    """ISO timestamp for when the interaction was created."""
    answered_at: str | None
    """ISO timestamp for when the interaction was answered."""


def add_help_interaction(
    database_connection: sqlite3.Connection,
    interaction: HelpInteraction,
) -> int:
    """Insert a help interaction and return its id."""
    return last_inserted_id(
        database_connection.execute(
            """
            insert into help_interactions
                (handle, source, visibility, question, response, topic_tags,
                created_at, answered_at)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                interaction.handle,
                interaction.source,
                interaction.visibility,
                interaction.question,
                interaction.response,
                dump_json({"tags": list(interaction.topic_tags)}),
                interaction.created_at,
                interaction.answered_at,
            ),
        ),
    )


def answer_help_interaction(
    database_connection: sqlite3.Connection,
    interaction_id: int,
    response: str,
    answered_at: str,
) -> None:
    """Attach a bot answer to an existing interaction."""
    database_connection.execute(
        """
        update help_interactions
        set response = ?, answered_at = ?
        where id = ?
        """,
        (response, answered_at, interaction_id),
    )


def get_help_interaction(
    database_connection: sqlite3.Connection,
    interaction_id: int,
) -> HelpInteraction | None:
    """Return a help interaction."""
    interaction_record = cast(
        "tuple[int, str, str, str, str, str | None, str, str, str | None] | None",
        database_connection.execute(
            """
            select id, handle, source, visibility, question, response, topic_tags,
                created_at, answered_at
            from help_interactions
            where id = ?
            """,
            (interaction_id,),
        ).fetchone(),
    )
    if interaction_record is None:
        return None
    return HelpInteraction(
        id=interaction_record[0],
        handle=interaction_record[1],
        source=interaction_record[2],
        visibility=interaction_record[3],
        question=interaction_record[4],
        response=interaction_record[5],
        topic_tags=topic_tags_from_json(interaction_record[6]),
        created_at=interaction_record[7],
        answered_at=interaction_record[8],
    )


def list_recent_help_interactions(
    database_connection: sqlite3.Connection,
    handle: str,
    limit: int,
    *,
    source: str | None = None,
    visibility: str | None = None,
) -> list[HelpInteraction]:
    """Return recent help interactions for one learner, optionally filtered."""
    interaction_records = cast(
        "list[tuple[int, str, str, str, str, str | None, str, str, str | None]]",
        database_connection.execute(
            """
            select id, handle, source, visibility, question, response, topic_tags,
                created_at, answered_at
            from help_interactions
            where handle = ?
                and (? is null or source = ?)
                and (? is null or visibility = ?)
            order by created_at desc, id desc
            limit ?
            """,
            (handle, source, source, visibility, visibility, limit),
        ).fetchall(),
    )
    return [
        _help_interaction_from_record(interaction_record)
        for interaction_record in interaction_records
    ]


def _help_interaction_from_record(
    interaction_record: tuple[int, str, str, str, str, str | None, str, str, str | None],
) -> HelpInteraction:
    return HelpInteraction(
        id=interaction_record[0],
        handle=interaction_record[1],
        source=interaction_record[2],
        visibility=interaction_record[3],
        question=interaction_record[4],
        response=interaction_record[5],
        topic_tags=topic_tags_from_json(interaction_record[6]),
        created_at=interaction_record[7],
        answered_at=interaction_record[8],
    )
