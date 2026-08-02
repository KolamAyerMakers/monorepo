"""Tests for the Kolam Ayer Makers classroom LLDAP group helper."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

from tests.support.paths import SALTSTACK_DIRECTORY


def _load_script() -> ModuleType:
    loader = importlib.machinery.SourceFileLoader(
        "lldap_ensure_group",
        str(
            SALTSTACK_DIRECTORY
            / "states/roles/kam-classroom/files/lldap_ensure_group.py"
        ),
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise AssertionError("Could not load lldap-ensure-group script")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_argument_parser_requires_group_and_gid_number(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that group management needs a name and gidNumber."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lldap-ensure-group",
            "humans",
            "--gid-number",
            "1001",
        ],
    )

    arguments = _load_script().parse_arguments()

    assert arguments.group == "humans"
    assert arguments.gid_number == 1001
    assert arguments.base_url == "http://127.0.0.1:17170/"
    assert arguments.admin_username == "admin"
    assert arguments.environment_file == "/etc/lldap/lldap.env"
    assert arguments.check is False


def test_ensure_group_creates_missing_group(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that an absent managed group is created."""
    script = _load_script()
    calls: list[dict[str, object]] = []

    def find_group(
        base_url: str,
        token: str,
        group_name: str,
    ) -> dict[str, object] | None:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        assert group_name == "humans"
        return None

    def create_group(
        base_url: str,
        token: str,
        group_name: str,
        group_id_number_value: int,
    ) -> None:
        calls.append(
            {
                "base_url": base_url,
                "token": token,
                "group_name": group_name,
                "group_id_number_value": group_id_number_value,
            }
        )

    monkeypatch.setattr(script, "find_group", find_group)
    monkeypatch.setattr(script, "create_group", create_group)

    script.ensure_group("http://127.0.0.1:17170/", "token", "humans", 1001, False)

    assert calls == [
        {
            "base_url": "http://127.0.0.1:17170/",
            "token": "token",
            "group_name": "humans",
            "group_id_number_value": 1001,
        }
    ]


def test_ensure_schema_treats_attribute_names_case_insensitively(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that an existing gidNumber schema attribute is detected."""
    script = _load_script()
    calls: list[dict[str, object]] = []

    def load_schema(base_url: str, token: str) -> dict[str, object]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return {"groupSchema": {"attributes": [{"name": "gidnumber"}]}}

    def ensure_group_attribute(
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

    monkeypatch.setattr(script, "load_schema", load_schema)
    monkeypatch.setattr(script, "ensure_group_attribute", ensure_group_attribute)

    script.ensure_schema("http://127.0.0.1:17170/", "token")

    assert calls == []


def test_ensure_schema_ignores_duplicate_group_attribute_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that schema creation tolerates attributes created by an earlier run."""
    script = _load_script()
    calls: list[dict[str, object]] = []

    def load_schema(base_url: str, token: str) -> dict[str, object]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return {"groupSchema": {"attributes": []}}

    def graphql(
        base_url: str,
        token: str,
        query: str,
        variables: dict[str, object],
    ) -> dict[str, object]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        assert "addGroupAttribute" in query
        calls.append(variables)
        raise script.LldapError(
            "UNIQUE constraint failed: group_attribute_schema.group_attribute_schema_name"
        )

    monkeypatch.setattr(script, "load_schema", load_schema)
    monkeypatch.setattr(script, "graphql", graphql)

    script.ensure_schema("http://127.0.0.1:17170/", "token")

    assert calls == [
        {
            "name": "gidNumber",
            "attributeType": "INTEGER",
            "isList": False,
            "isVisible": True,
            "isEditable": False,
        }
    ]


def test_ensure_group_check_rejects_missing_group(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that check mode reports a missing managed group."""
    script = _load_script()

    def find_group(
        base_url: str,
        token: str,
        group_name: str,
    ) -> dict[str, object] | None:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        assert group_name == "humans"
        return None

    monkeypatch.setattr(script, "find_group", find_group)

    with pytest.raises(script.LldapError) as error:
        script.ensure_group("http://127.0.0.1:17170/", "token", "humans", 1001, True)

    assert str(error.value) == "Group humans does not exist"


def test_ensure_group_updates_missing_gid_number(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that a managed group without gidNumber is repaired."""
    script = _load_script()
    calls: list[dict[str, object]] = []

    def find_group(
        base_url: str,
        token: str,
        group_name: str,
    ) -> dict[str, object] | None:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        assert group_name == "humans"
        return {"id": 42, "displayName": "humans", "attributes": []}

    def update_group_id_number(
        base_url: str,
        token: str,
        group_identifier: int,
        group_id_number_value: int,
    ) -> None:
        calls.append(
            {
                "base_url": base_url,
                "token": token,
                "group_identifier": group_identifier,
                "group_id_number_value": group_id_number_value,
            }
        )

    monkeypatch.setattr(script, "find_group", find_group)
    monkeypatch.setattr(script, "update_group_id_number", update_group_id_number)

    script.ensure_group("http://127.0.0.1:17170/", "token", "humans", 1001, False)

    assert calls == [
        {
            "base_url": "http://127.0.0.1:17170/",
            "token": "token",
            "group_identifier": 42,
            "group_id_number_value": 1001,
        }
    ]


def test_ensure_group_rejects_conflicting_gid_number(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that a conflicting gidNumber is not changed silently."""
    script = _load_script()

    def find_group(
        base_url: str,
        token: str,
        group_name: str,
    ) -> dict[str, object] | None:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        assert group_name == "humans"
        return {
            "id": 42,
            "displayName": "humans",
            "attributes": [{"name": "gidNumber", "value": ["2000"]}],
        }

    monkeypatch.setattr(script, "find_group", find_group)

    with pytest.raises(script.LldapError) as error:
        script.ensure_group("http://127.0.0.1:17170/", "token", "humans", 1001, False)

    assert str(error.value) == "Group humans has gidNumber 2000, expected 1001"


def test_main_ensures_group_and_prints_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that the main flow manages the requested group."""
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
            "lldap-ensure-group",
            "humans",
            "--gid-number",
            "1001",
            "--environment-file",
            str(environment_file),
        ],
    )

    def login(base_url: str, username: str, password: str) -> str:
        calls.append({"base_url": base_url, "username": username, "password": password})
        return "token"

    monkeypatch.setattr(script, "login", login)

    def ensure_schema(base_url: str, token: str) -> None:
        calls.append({"schema_base_url": base_url, "schema_token": token})

    monkeypatch.setattr(script, "ensure_schema", ensure_schema)

    def ensure_group(
        base_url: str,
        token: str,
        group_name: str,
        group_id_number_value: int,
        check_only: bool,
    ) -> None:
        calls.append(
            {
                "base_url": base_url,
                "token": token,
                "group_name": group_name,
                "group_id_number_value": group_id_number_value,
                "check_only": check_only,
            }
        )

    monkeypatch.setattr(script, "ensure_group", ensure_group)

    assert script.main() == 0
    assert calls == [
        {
            "base_url": "http://127.0.0.1:17170/",
            "username": "admin",
            "password": "admin-secret",
        },
        {
            "schema_base_url": "http://127.0.0.1:17170/",
            "schema_token": "token",
        },
        {
            "base_url": "http://127.0.0.1:17170/",
            "token": "token",
            "group_name": "humans",
            "group_id_number_value": 1001,
            "check_only": False,
        },
    ]
    assert capsys.readouterr().out == "humans\n"
