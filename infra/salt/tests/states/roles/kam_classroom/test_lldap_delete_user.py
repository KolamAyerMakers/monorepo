"""Tests for the Kolam Ayer Makers classroom LLDAP user deletion helper."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import subprocess
import sys
import textwrap
from pathlib import Path
from types import ModuleType

import pytest

from tests.support.paths import SALTSTACK_DIRECTORY


def _load_script() -> ModuleType:
    loader = importlib.machinery.SourceFileLoader(
        "lldap_delete_user",
        str(
            SALTSTACK_DIRECTORY
            / "states/roles/kam-classroom/files/lldap_delete_user.py"
        ),
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise AssertionError("Could not load lldap-delete-user script")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_argument_parser_accepts_username(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that only a username is required."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lldap-delete-user",
            "alice",
        ],
    )

    arguments = _load_script().parse_arguments()

    assert arguments.username == "alice"
    assert arguments.base_url == "http://127.0.0.1:17170/"
    assert arguments.admin_username == "admin"
    assert arguments.environment_file == "/etc/lldap/lldap.env"
    assert arguments.skip_sss_cache is False


def test_delete_user_calls_lldap_graphql_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that user deletion uses the LLDAP GraphQL mutation."""
    script = _load_script()
    calls: list[dict[str, object]] = []

    def graphql(
        base_url: str,
        token: str,
        query: str,
        variables: dict[str, object],
    ) -> dict[str, object]:
        calls.append(
            {
                "base_url": base_url,
                "token": token,
                "query": textwrap.dedent(query).strip(),
                "variables": variables,
            }
        )
        return {}

    monkeypatch.setattr(script, "graphql", graphql)

    script.delete_user("http://127.0.0.1:17170/", "token", "alice")

    assert calls == [
        {
            "base_url": "http://127.0.0.1:17170/",
            "token": "token",
            "query": textwrap.dedent(
                """\
                mutation DeleteUser($userId: String!) {
                  deleteUser(userId: $userId) { ok }
                }
                """
            ).strip(),
            "variables": {"userId": "alice"},
        }
    ]


def test_invalidate_sss_cache_runs_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that deleting a user invalidates the SSSD user cache."""
    script = _load_script()
    calls: list[dict[str, object]] = []

    class ExistingPath:
        def __init__(self, path: str) -> None:
            self.path: str
            self.path = path

        def is_file(self) -> bool:
            return self.path == "/usr/sbin/sss_cache"

    def run(
        arguments: list[str],
        *,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        calls.append({"arguments": arguments, "check": check})
        return subprocess.CompletedProcess(arguments, 0)

    monkeypatch.setattr(script, "Path", ExistingPath)
    monkeypatch.setattr(script.subprocess, "run", run)

    script.invalidate_sss_cache("alice")

    assert calls == [
        {"arguments": ["/usr/sbin/sss_cache", "-u", "alice"], "check": True}
    ]


def test_invalidate_sss_cache_skips_missing_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that cache invalidation is optional when SSSD is absent."""
    script = _load_script()
    calls: list[dict[str, object]] = []

    class MissingPath:
        def __init__(self, path: str) -> None:
            self.path: str
            self.path = path

        def is_file(self) -> bool:
            return False

    def run(
        arguments: list[str],
        *,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        calls.append({"arguments": arguments, "check": check})
        return subprocess.CompletedProcess(arguments, 0)

    monkeypatch.setattr(script, "Path", MissingPath)
    monkeypatch.setattr(script.subprocess, "run", run)

    script.invalidate_sss_cache("alice")

    assert calls == []


def test_main_deletes_user_and_invalidates_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that the main flow deletes the user and clears the cache."""
    script = _load_script()
    environment_file = tmp_path / "lldap.env"
    _ = environment_file.write_text(
        "LLDAP_LDAP_USER_PASS=admin-secret\n", encoding="utf-8"
    )
    calls: list[dict[str, str]] = []

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lldap-delete-user",
            "alice",
            "--environment-file",
            str(environment_file),
        ],
    )

    def login(base_url: str, username: str, password: str) -> str:
        calls.append({"base_url": base_url, "username": username, "password": password})
        return "token"

    monkeypatch.setattr(script, "login", login)

    def delete_user(base_url: str, token: str, username: str) -> None:
        calls.append({"base_url": base_url, "token": token, "username": username})

    monkeypatch.setattr(script, "delete_user", delete_user)

    def invalidate_sss_cache(username: str) -> None:
        calls.append({"cache_username": username})

    monkeypatch.setattr(script, "invalidate_sss_cache", invalidate_sss_cache)

    assert script.main() == 0
    assert calls == [
        {
            "base_url": "http://127.0.0.1:17170/",
            "username": "admin",
            "password": "admin-secret",
        },
        {
            "base_url": "http://127.0.0.1:17170/",
            "token": "token",
            "username": "alice",
        },
        {"cache_username": "alice"},
    ]
    assert capsys.readouterr().out == "alice\n"


def test_main_can_skip_sss_cache_invalidation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that cache invalidation can be skipped explicitly."""
    script = _load_script()
    environment_file = tmp_path / "lldap.env"
    _ = environment_file.write_text(
        "LLDAP_LDAP_USER_PASS=admin-secret\n", encoding="utf-8"
    )
    calls: list[dict[str, str]] = []

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lldap-delete-user",
            "alice",
            "--skip-sss-cache",
            "--environment-file",
            str(environment_file),
        ],
    )

    def login(base_url: str, username: str, password: str) -> str:
        assert base_url == "http://127.0.0.1:17170/"
        assert username == "admin"
        assert password == "admin-secret"
        return "token"

    monkeypatch.setattr(script, "login", login)

    def delete_user(base_url: str, token: str, username: str) -> None:
        calls.append({"base_url": base_url, "token": token, "username": username})

    monkeypatch.setattr(script, "delete_user", delete_user)

    def invalidate_sss_cache(username: str) -> None:
        calls.append({"cache_username": username})

    monkeypatch.setattr(script, "invalidate_sss_cache", invalidate_sss_cache)

    assert script.main() == 0
    assert calls == [
        {
            "base_url": "http://127.0.0.1:17170/",
            "token": "token",
            "username": "alice",
        }
    ]
    assert capsys.readouterr().out == "alice\n"
