"""Tests for learner web-service Caddy route rendering."""

from __future__ import annotations

import pwd
from pathlib import Path
from typing import TYPE_CHECKING

from maker_guide.cli import render_learner_routes as learner_routes
from maker_guide.repositories.helpers import connect_database
from maker_guide.repositories.learner import Learner, get_learner, upsert_learner

if TYPE_CHECKING:
    import pytest


def test_render_learner_routes_uses_registered_uid() -> None:
    """Each mapped learner serves canonical Astro URLs and root URLs."""
    rendered = learner_routes.render_learner_routes(
        "lf2607.kolamayermakers.org",
        [
            Learner(
                handle="alice",
                joined_at="2026-07-17T00:00:00Z",
                tagline=None,
                created_at="2026-07-17T00:00:00Z",
                uid=20001,
            )
        ],
        frozenset({"alice"}),
    )

    assert rendered == (
        "alice.lf2607.kolamayermakers.org {\n"
        "    encode zstd gzip\n"
        "    @canonical_path path /~alice /~alice/*\n"
        "    handle @canonical_path {\n"
        "        uri strip_prefix /~alice\n"
        "        reverse_proxy 127.0.0.1:30001\n"
        "    }\n"
        "    reverse_proxy 127.0.0.1:30001\n"
        "}\n"
    )


def test_render_learner_routes_omits_unmapped_learners() -> None:
    """Pre-existing rows without a captured UID cannot receive a route."""
    assert (
        learner_routes.render_learner_routes(
            "lf2607.kolamayermakers.org",
            [
                Learner(
                    handle="alice",
                    joined_at="2026-07-17T00:00:00Z",
                    tagline=None,
                    created_at="2026-07-17T00:00:00Z",
                )
            ],
            frozenset({"alice"}),
        )
        == "# No learner routes.\n"
    )


def test_render_learner_routes_includes_managed_course_participants() -> None:
    """Managed course participants receive learner web-service routes."""
    assert learner_routes.render_learner_routes(
        "lf2607.kolamayermakers.org",
        [
            Learner(
                handle="mentor",
                joined_at="2026-07-17T00:00:00Z",
                tagline=None,
                created_at="2026-07-17T00:00:00Z",
                uid=10001,
            ),
        ],
        frozenset({"mentor"}),
    ) == (
        "mentor.lf2607.kolamayermakers.org {\n"
        "    encode zstd gzip\n"
        "    @canonical_path path /~mentor /~mentor/*\n"
        "    handle @canonical_path {\n"
        "        uri strip_prefix /~mentor\n"
        "        reverse_proxy 127.0.0.1:20001\n"
        "    }\n"
        "    reverse_proxy 127.0.0.1:20001\n"
        "}\n"
    )


def test_capture_missing_uids_persists_legacy_mapping(
    migrated_database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Legacy learner rows acquire their immutable mapping before routes render."""
    with connect_database(migrated_database_path) as database_connection:
        upsert_learner(
            database_connection,
            Learner(
                handle="alice",
                joined_at="2026-07-17T00:00:00Z",
                tagline=None,
                created_at="2026-07-17T00:00:00Z",
            ),
        )
        monkeypatch.setattr(learner_routes.pwd, "getpwnam", _getpwnam)
        learner_routes.capture_missing_uids(database_connection)

        learner = get_learner(database_connection, "alice")

    assert learner is not None
    assert learner.uid == 20001


def _getpwnam(_handle: str) -> pwd.struct_passwd:
    return pwd.struct_passwd(("alice", "x", 20001, 20001, "", "/home/alice", "/bin/bash"))
