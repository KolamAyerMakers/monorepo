"""Render exact Caddy routes for registered learner web services."""

from __future__ import annotations

import pwd
import re
import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, cast

import typer

from maker_guide.curriculum.catalogs import DEFAULT_COURSE_ID
from maker_guide.identity.policy import is_managed_uid
from maker_guide.repositories.cohort_membership import list_memberships
from maker_guide.repositories.helpers import connect_database, transaction
from maker_guide.repositories.learner import Learner, list_learners

_DOMAIN_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9-]+)+")
_HANDLE_PATTERN = re.compile(r"[a-z][a-z0-9-]{1,31}")
_PORT_OFFSET = 10000

app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)


def run(arguments: Sequence[str] | None = None) -> int:
    """Run the Typer app for tests."""
    result = cast(
        "object",
        app(args=list(arguments) if arguments is not None else None, standalone_mode=False),
    )
    return result if isinstance(result, int) else 0


@app.command()
def render(
    database_path: Annotated[Path, typer.Option("--database")],
    domain: Annotated[str, typer.Option("--domain")],
) -> None:
    """Write Caddy site blocks to standard output."""
    with connect_database(database_path) as database_connection:
        capture_missing_uids(database_connection)
        participant_handles = frozenset(
            membership.handle
            for membership in list_memberships(database_connection, DEFAULT_COURSE_ID)
        )
        typer.echo(
            render_learner_routes(
                domain,
                list_learners(database_connection),
                participant_handles,
            ),
            nl=False,
        )


def render_learner_routes(
    domain: str,
    learners: list[Learner],
    participant_handles: frozenset[str],
) -> str:
    """Render one exact loopback proxy site block for each mapped learner."""
    if _DOMAIN_PATTERN.fullmatch(domain) is None:
        raise ValueError(f"unsafe domain: {domain}")
    route_blocks: list[str] = []
    for learner in learners:
        if learner.handle not in participant_handles or learner.uid is None:
            continue
        if _HANDLE_PATTERN.fullmatch(learner.handle) is None:
            raise ValueError(f"unsafe learner handle: {learner.handle}")
        if not is_managed_uid(learner.uid):
            continue
        route_blocks.append(
            "".join(
                (
                    f"{learner.handle}.{domain} {{\n",
                    "    encode zstd gzip\n",
                    f"    @canonical_path path /~{learner.handle} /~{learner.handle}/*\n",
                    "    handle @canonical_path {\n",
                    f"        uri strip_prefix /~{learner.handle}\n",
                    f"        reverse_proxy 127.0.0.1:{_PORT_OFFSET + learner.uid}\n",
                    "    }\n",
                    f"    reverse_proxy 127.0.0.1:{_PORT_OFFSET + learner.uid}\n",
                    "}\n",
                )
            )
        )
    return "\n".join(route_blocks) or "# No learner routes.\n"


def capture_missing_uids(database_connection: sqlite3.Connection) -> None:
    """Persist mappings for learner rows created before routing was introduced."""
    with transaction(database_connection):
        for learner in list_learners(database_connection):
            if learner.uid is not None:
                continue
            uid = pwd.getpwnam(learner.handle).pw_uid
            if not is_managed_uid(uid):
                continue
            database_connection.execute(
                "update learners set uid = ? where handle = ? and uid is null",
                (uid, learner.handle),
            )
