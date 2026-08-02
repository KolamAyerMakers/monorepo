"""Tests for the Kolam Ayer Makers classroom LLDAP managed user helper."""

from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

from tests.support.paths import SALTSTACK_DIRECTORY


def _load_script() -> ModuleType:
    loader = importlib.machinery.SourceFileLoader(
        "lldap_ensure_user",
        str(
            SALTSTACK_DIRECTORY
            / "states/roles/kam-classroom/files/lldap_ensure_user.py"
        ),
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise AssertionError("Could not load lldap-ensure-user script")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_argument_parser_requires_managed_user_attributes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that managed users require explicit POSIX identity data."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lldap-ensure-user",
            "guide",
            "--uid-number",
            "9000",
            "--display-name",
            "TheGuide",
            "--email",
            "guide@kam-classroom-dev",
            "--home-directory",
            "/var/lib/guide",
            "--shell",
            "/usr/sbin/nologin",
            "--primary-group",
            "guide",
            "--secondary-group",
            "irc-bots",
            "--ssh-public-key",
            "ssh-rsa AAAATEST cardno:25_939_134",
        ],
    )

    arguments = _load_script().parse_arguments()

    assert arguments.username == "guide"
    assert arguments.uid_number == 9000
    assert arguments.display_name == "TheGuide"
    assert arguments.email == "guide@kam-classroom-dev"
    assert arguments.home_directory == "/var/lib/guide"
    assert arguments.shell == "/usr/sbin/nologin"
    assert arguments.primary_group == "guide"
    assert arguments.secondary_group_names == ["irc-bots"]
    assert arguments.ssh_public_keys == ["ssh-rsa AAAATEST cardno:25_939_134"]
    assert arguments.check is False


def test_ensure_schema_adds_missing_user_posix_attributes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that managed users prepare the LLDAP POSIX user schema."""
    script = _load_script()
    calls: list[dict[str, object]] = []

    def load_schema(base_url: str, token: str) -> dict[str, object]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return {
            "userSchema": {
                "attributes": [{"name": "uidnumber"}],
                "ldapObjectClasses": [],
            }
        }

    def ensure_user_attribute(
        base_url: str,
        token: str,
        name: str,
        attribute_type: str,
        is_list: bool,
        is_visible: bool,
        is_editable: bool,
    ) -> None:
        calls.append(
            {
                "base_url": base_url,
                "token": token,
                "name": name,
                "attribute_type": attribute_type,
                "is_list": is_list,
                "is_visible": is_visible,
                "is_editable": is_editable,
            }
        )

    def graphql(
        base_url: str,
        token: str,
        query: str,
        variables: dict[str, object],
    ) -> dict[str, object]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        assert "addUserObjectClass" in query
        calls.append(variables)
        return {"ok": True}

    monkeypatch.setattr(script, "load_schema", load_schema)
    monkeypatch.setattr(script, "ensure_user_attribute", ensure_user_attribute)
    monkeypatch.setattr(script, "graphql", graphql)

    script.ensure_schema("http://127.0.0.1:17170/", "token")

    assert calls == [
        {
            "base_url": "http://127.0.0.1:17170/",
            "token": "token",
            "name": "gidNumber",
            "attribute_type": "INTEGER",
            "is_list": False,
            "is_visible": True,
            "is_editable": False,
        },
        {
            "base_url": "http://127.0.0.1:17170/",
            "token": "token",
            "name": "homeDirectory",
            "attribute_type": "STRING",
            "is_list": False,
            "is_visible": True,
            "is_editable": False,
        },
        {
            "base_url": "http://127.0.0.1:17170/",
            "token": "token",
            "name": "unixShell",
            "attribute_type": "STRING",
            "is_list": False,
            "is_visible": True,
            "is_editable": False,
        },
        {
            "base_url": "http://127.0.0.1:17170/",
            "token": "token",
            "name": "sshPublicKey",
            "attribute_type": "STRING",
            "is_list": True,
            "is_visible": True,
            "is_editable": True,
        },
        {"name": "posixAccount"},
    ]


def test_ensure_user_creates_missing_user_and_memberships(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that a missing managed user is created in LDAP only."""
    script = _load_script()
    calls: list[dict[str, object]] = []
    arguments = _managed_user_arguments()

    def load_groups(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return _groups()

    def load_users(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return []

    monkeypatch.setattr(script, "load_groups", load_groups)
    monkeypatch.setattr(script, "load_users", load_users)

    def create_user(
        command_arguments: object,
        base_url: str,
        token: str,
        group_id_number_value: int,
    ) -> None:
        assert command_arguments == arguments
        calls.append(
            {
                "operation": "create_user",
                "base_url": base_url,
                "token": token,
                "group_id_number_value": group_id_number_value,
            }
        )

    def add_user_to_group(
        base_url: str,
        token: str,
        username: str,
        group_identifier: int,
    ) -> None:
        calls.append(
            {
                "operation": "add_user_to_group",
                "base_url": base_url,
                "token": token,
                "username": username,
                "group_identifier": group_identifier,
            }
        )

    monkeypatch.setattr(script, "create_user", create_user)
    monkeypatch.setattr(script, "add_user_to_group", add_user_to_group)

    assert script.ensure_user(arguments, "http://127.0.0.1:17170/", "token", False)
    assert calls == [
        {
            "operation": "create_user",
            "base_url": "http://127.0.0.1:17170/",
            "token": "token",
            "group_id_number_value": 9000,
        },
        {
            "operation": "add_user_to_group",
            "base_url": "http://127.0.0.1:17170/",
            "token": "token",
            "username": "guide",
            "group_identifier": 90,
        },
        {
            "operation": "add_user_to_group",
            "base_url": "http://127.0.0.1:17170/",
            "token": "token",
            "username": "guide",
            "group_identifier": 91,
        },
    ]


def test_ensure_user_check_rejects_missing_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that check mode reports absent managed users."""
    script = _load_script()

    def load_groups(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return _groups()

    def load_users(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return []

    monkeypatch.setattr(script, "load_groups", load_groups)
    monkeypatch.setattr(script, "load_users", load_users)

    with pytest.raises(script.LldapError) as error:
        script.ensure_user(
            _managed_user_arguments(),
            "http://127.0.0.1:17170/",
            "token",
            True,
        )

    assert str(error.value) == "User guide does not exist"


def test_ensure_user_updates_missing_attributes_and_membership(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that managed users are repaired without provisioning Forgejo."""
    script = _load_script()
    calls: list[dict[str, object]] = []
    arguments = _managed_user_arguments()

    def load_groups(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return _groups()

    def load_users(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return [
            {
                "id": "guide",
                "email": "old@example.test",
                "displayName": "Old TheGuide",
                "attributes": [
                    {"name": "uidNumber", "value": ["9000"]},
                    {"name": "gidNumber", "value": ["9000"]},
                    {"name": "homeDirectory", "value": ["/old"]},
                ],
                "groups": [{"id": 90, "displayName": "guide"}],
            }
        ]

    monkeypatch.setattr(script, "load_groups", load_groups)
    monkeypatch.setattr(script, "load_users", load_users)

    def update_user(
        command_arguments: object,
        base_url: str,
        token: str,
        changed_attributes: dict[str, str],
    ) -> None:
        assert command_arguments == arguments
        calls.append(
            {
                "operation": "update_user",
                "base_url": base_url,
                "token": token,
                "changed_attributes": changed_attributes,
            }
        )

    def add_user_to_group(
        base_url: str,
        token: str,
        username: str,
        group_identifier: int,
    ) -> None:
        calls.append(
            {
                "operation": "add_user_to_group",
                "base_url": base_url,
                "token": token,
                "username": username,
                "group_identifier": group_identifier,
            }
        )

    monkeypatch.setattr(script, "update_user", update_user)
    monkeypatch.setattr(script, "add_user_to_group", add_user_to_group)

    assert script.ensure_user(arguments, "http://127.0.0.1:17170/", "token", False)
    assert calls == [
        {
            "operation": "update_user",
            "base_url": "http://127.0.0.1:17170/",
            "token": "token",
            "changed_attributes": {
                "homeDirectory": ["/var/lib/guide"],
                "unixShell": ["/usr/sbin/nologin"],
            },
        },
        {
            "operation": "add_user_to_group",
            "base_url": "http://127.0.0.1:17170/",
            "token": "token",
            "username": "guide",
            "group_identifier": 91,
        },
    ]


def test_ensure_user_rejects_conflicting_uid_number(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that static UIDs cannot be reused by another LDAP user."""
    script = _load_script()

    def load_groups(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return _groups()

    def load_users(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return [
            {
                "id": "other",
                "email": "other@kam-classroom-dev",
                "displayName": "Other",
                "attributes": [{"name": "uidNumber", "value": ["9000"]}],
                "groups": [],
            }
        ]

    monkeypatch.setattr(script, "load_groups", load_groups)
    monkeypatch.setattr(script, "load_users", load_users)

    with pytest.raises(script.LldapError) as error:
        script.ensure_user(
            _managed_user_arguments(),
            "http://127.0.0.1:17170/",
            "token",
            False,
        )

    assert str(error.value) == "uidNumber 9000 is already used by other"


def test_ensure_user_updates_missing_ssh_public_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that managed users can receive an LDAP SSH public key."""
    script = _load_script()
    calls: list[dict[str, object]] = []
    arguments = _managed_user_arguments(
        ssh_public_keys=["ssh-rsa AAAATEST cardno:25_939_134"]
    )

    def load_groups(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return _groups()

    def load_users(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return [
            {
                "id": "guide",
                "email": "guide@kam-classroom-dev",
                "displayName": "TheGuide",
                "attributes": [
                    {"name": "uidNumber", "value": ["9000"]},
                    {"name": "gidNumber", "value": ["9000"]},
                    {"name": "homeDirectory", "value": ["/var/lib/guide"]},
                    {"name": "unixShell", "value": ["/usr/sbin/nologin"]},
                ],
                "groups": [
                    {"id": 90, "displayName": "guide"},
                    {"id": 91, "displayName": "irc-bots"},
                ],
            }
        ]

    def update_user(
        command_arguments: object,
        base_url: str,
        token: str,
        changed_attributes: dict[str, list[str]],
    ) -> None:
        assert command_arguments == arguments
        calls.append(
            {
                "operation": "update_user",
                "base_url": base_url,
                "token": token,
                "changed_attributes": changed_attributes,
            }
        )

    monkeypatch.setattr(script, "load_groups", load_groups)
    monkeypatch.setattr(script, "load_users", load_users)
    monkeypatch.setattr(script, "update_user", update_user)

    assert script.ensure_user(arguments, "http://127.0.0.1:17170/", "token", False)
    assert calls == [
        {
            "operation": "update_user",
            "base_url": "http://127.0.0.1:17170/",
            "token": "token",
            "changed_attributes": {
                "sshPublicKey": ["ssh-rsa AAAATEST cardno:25_939_134"]
            },
        }
    ]


def test_main_ensures_managed_user_and_prints_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that the main flow manages the requested LDAP user."""
    script = _load_script()
    environment_file = tmp_path / "lldap.env"
    _ = environment_file.write_text(
        "LLDAP_LDAP_USER_PASS=admin-secret\n", encoding="utf-8"
    )
    calls: list[dict[str, object]] = []

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lldap-ensure-user",
            "guide",
            "--uid-number",
            "9000",
            "--display-name",
            "TheGuide",
            "--email",
            "guide@kam-classroom-dev",
            "--home-directory",
            "/var/lib/guide",
            "--shell",
            "/usr/sbin/nologin",
            "--primary-group",
            "guide",
            "--secondary-group",
            "irc-bots",
            "--environment-file",
            str(environment_file),
        ],
    )

    def login(base_url: str, username: str, password: str) -> str:
        calls.append({"base_url": base_url, "username": username, "password": password})
        return "token"

    def ensure_schema(base_url: str, token: str) -> None:
        calls.append({"schema_base_url": base_url, "schema_token": token})

    def ensure_user(
        arguments: object,
        base_url: str,
        token: str,
        check_only: bool,
    ) -> bool:
        calls.append(
            {
                "arguments": arguments,
                "base_url": base_url,
                "token": token,
                "check_only": check_only,
            }
        )
        return True

    monkeypatch.setattr(script, "login", login)
    monkeypatch.setattr(script, "ensure_schema", ensure_schema)
    monkeypatch.setattr(script, "ensure_user", ensure_user)

    def invalidate_sss_cache(username: str) -> None:
        assert username == "guide"

    monkeypatch.setattr(script, "invalidate_sss_cache", invalidate_sss_cache)

    assert script.main() == 0
    assert calls[0:2] == [
        {
            "base_url": "http://127.0.0.1:17170/",
            "username": "admin",
            "password": "admin-secret",
        },
        {
            "schema_base_url": "http://127.0.0.1:17170/",
            "schema_token": "token",
        },
    ]
    assert calls[2]["base_url"] == "http://127.0.0.1:17170/"
    assert calls[2]["token"] == "token"
    assert calls[2]["check_only"] is False
    assert capsys.readouterr().out == "guide\n"


def test_migrate_group_members_adds_only_missing_target_memberships(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that legacy members retain their membership while gaining replacements."""
    script = _load_script()
    memberships = {
        "alice": {"lf2607"},
        "bob": {"lf2607", "linux-foundations"},
        "carol": {"humans"},
    }
    additions: list[tuple[str, int]] = []

    def load_groups(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return [
            {
                "id": group_identifier,
                "displayName": group_name,
                "attributes": [{"name": "gidNumber", "value": ["1000"]}],
            }
            for group_identifier, group_name in enumerate(
                ("lf2607", "linux-foundations", "students"), start=1
            )
        ]

    def load_users(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return [
            {
                "id": username,
                "groups": [{"displayName": group_name} for group_name in group_names],
            }
            for username, group_names in memberships.items()
        ]

    def add_user_to_group(
        base_url: str,
        token: str,
        username: str,
        group_identifier: int,
    ) -> None:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        group_names = {1: "lf2607", 2: "linux-foundations", 3: "students"}
        memberships[username].add(group_names[group_identifier])
        additions.append((username, group_identifier))

    monkeypatch.setattr(script, "load_groups", load_groups)
    monkeypatch.setattr(script, "load_users", load_users)
    monkeypatch.setattr(script, "add_user_to_group", add_user_to_group)

    assert script.migrate_group_members(
        "http://127.0.0.1:17170/",
        "token",
        "lf2607",
        ["linux-foundations", "students"],
        False,
    )
    assert additions == [("alice", 2), ("alice", 3), ("bob", 3)]
    assert memberships["alice"] == {"lf2607", "linux-foundations", "students"}
    assert memberships["bob"] == {"lf2607", "linux-foundations", "students"}
    assert not script.migrate_group_members(
        "http://127.0.0.1:17170/",
        "token",
        "lf2607",
        ["linux-foundations", "students"],
        False,
    )
    assert additions == [("alice", 2), ("alice", 3), ("bob", 3)]


def test_migrate_group_members_handles_no_legacy_members(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that no legacy members leave LDAP unchanged."""
    script = _load_script()
    additions: list[tuple[str, int]] = []

    def load_groups(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return _migration_groups()

    def load_users(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return [{"id": "alice", "groups": [{"displayName": "humans"}]}]

    def add_user_to_group(
        base_url: str,
        token: str,
        username: str,
        group_identifier: int,
    ) -> None:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        additions.append((username, group_identifier))

    monkeypatch.setattr(script, "load_groups", load_groups)
    monkeypatch.setattr(script, "load_users", load_users)
    monkeypatch.setattr(script, "add_user_to_group", add_user_to_group)

    assert not script.migrate_group_members(
        "http://127.0.0.1:17170/",
        "token",
        "lf2607",
        ["linux-foundations", "students"],
        False,
    )
    assert additions == []


def test_invalidate_sss_cache_ignores_missing_cache_entry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that new LDAP users do not fail when SSSD has no cache entry."""
    script = _load_script()

    def is_file(self: Path) -> bool:
        assert str(self) == "/usr/sbin/sss_cache"
        return True

    def run(
        arguments: list[str],
        *,
        check: bool,
        stderr: int,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        assert arguments == ["/usr/sbin/sss_cache", "-u", "guide"]
        assert check is False
        assert stderr == subprocess.PIPE
        assert text is True
        return subprocess.CompletedProcess(
            arguments,
            2,
            stderr="No cache object matched the specified search\n",
        )

    monkeypatch.setattr(script.Path, "is_file", is_file)
    monkeypatch.setattr(script.subprocess, "run", run)

    script.invalidate_sss_cache("guide")


def test_invalidate_sss_cache_raises_unexpected_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that real SSSD cache invalidation failures are still surfaced."""
    script = _load_script()

    def is_file(self: Path) -> bool:
        assert str(self) == "/usr/sbin/sss_cache"
        return True

    def run(
        arguments: list[str],
        *,
        check: bool,
        stderr: int,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        assert arguments == ["/usr/sbin/sss_cache", "-u", "guide"]
        assert check is False
        assert stderr == subprocess.PIPE
        assert text is True
        return subprocess.CompletedProcess(arguments, 1, stderr="boom\n")

    monkeypatch.setattr(script.Path, "is_file", is_file)
    monkeypatch.setattr(script.subprocess, "run", run)

    with pytest.raises(subprocess.CalledProcessError) as error:
        script.invalidate_sss_cache("guide")

    assert error.value.returncode == 1
    assert error.value.stderr == "boom\n"


def _managed_user_arguments(
    ssh_public_keys: list[str] | None = None,
) -> argparse.Namespace:
    return argparse.Namespace(
        username="guide",
        uid_number=9000,
        display_name="TheGuide",
        email="guide@kam-classroom-dev",
        home_directory="/var/lib/guide",
        shell="/usr/sbin/nologin",
        primary_group="guide",
        secondary_group_names=["irc-bots"],
        ssh_public_keys=ssh_public_keys or [],
    )


def _groups() -> list[dict[str, object]]:
    return [
        {
            "id": 90,
            "displayName": "guide",
            "attributes": [{"name": "gidNumber", "value": ["9000"]}],
        },
        {
            "id": 91,
            "displayName": "irc-bots",
            "attributes": [{"name": "gidNumber", "value": ["9001"]}],
        },
    ]


def _migration_groups() -> list[dict[str, object]]:
    return [
        {
            "id": group_identifier,
            "displayName": group_name,
            "attributes": [{"name": "gidNumber", "value": ["1000"]}],
        }
        for group_identifier, group_name in enumerate(
            ("lf2607", "linux-foundations", "students"), start=1
        )
    ]
