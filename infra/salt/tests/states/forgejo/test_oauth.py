"""Tests for Forgejo OAuth source reconciliation."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from tests.support.paths import SALTSTACK_DIRECTORY


def test_oauth_source_check_detects_restored_discovery_url(tmp_path: Path) -> None:
    """Test that a restored production issuer requires reconciliation on dev."""
    database_path = tmp_path / "forgejo.db"
    secret_path = tmp_path / "oauth-secret"
    configuration_path = tmp_path / "app.ini"
    _ = secret_path.write_text("secret\n", encoding="utf-8")
    _ = configuration_path.write_text(
        f"[database]\nPATH = {database_path}\n", encoding="utf-8"
    )
    with sqlite3.connect(database_path) as connection:
        _ = connection.execute(
            "CREATE TABLE login_source (type INTEGER, name TEXT, cfg TEXT)"
        )
        _ = connection.execute(
            "INSERT INTO login_source VALUES (?, ?, ?)",
            (
                6,
                "authelia",
                json.dumps(
                    {
                        "Provider": "openidConnect",
                        "ClientID": "forgejo",
                        "ClientSecret": "secret",
                        "OpenIDConnectAutoDiscoveryURL": (
                            "https://lf-dev.kolamayermakers.org/auth/.well-known/"
                            "openid-configuration"
                        ),
                        "Scopes": ["openid", "email", "profile", "groups"],
                        "GroupClaimName": "groups",
                    }
                ),
            ),
        )

    command = [
        sys.executable,
        str(SALTSTACK_DIRECTORY / "states/forgejo/files/forgejo_sync_oauth_source.py"),
        "--name",
        "authelia",
        "--provider",
        "openidConnect",
        "--client-id",
        "forgejo",
        "--client-secret-file",
        str(secret_path),
        "--auto-discover-url",
        "https://lf-dev.kolamayermakers.org/auth/.well-known/openid-configuration",
        "--scope",
        "openid",
        "--scope",
        "email",
        "--scope",
        "profile",
        "--scope",
        "groups",
        "--group-claim-name",
        "groups",
        "--configuration-file",
        str(configuration_path),
        "--check",
    ]

    assert subprocess.run(command, check=False).returncode == 0

    with sqlite3.connect(database_path) as connection:
        _ = connection.execute(
            "UPDATE login_source SET cfg = ?",
            (
                json.dumps(
                    {
                        "Provider": "openidConnect",
                        "ClientID": "forgejo",
                        "ClientSecret": "secret",
                        "OpenIDConnectAutoDiscoveryURL": (
                            "https://lf2607.kolamayermakers.org/auth/.well-known/"
                            "openid-configuration"
                        ),
                        "Scopes": ["openid", "email", "profile", "groups"],
                        "GroupClaimName": "groups",
                    }
                ),
            ),
        )

    assert subprocess.run(command, check=False).returncode == 1
