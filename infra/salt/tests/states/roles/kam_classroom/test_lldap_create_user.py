"""Tests for the Kolam Ayer Makers classroom LLDAP user creation helper."""

# pyright: reportUnknownArgumentType=false, reportUnknownLambdaType=false

from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import io
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

from tests.support.paths import SALTSTACK_DIRECTORY


def _load_script() -> ModuleType:
    loader = importlib.machinery.SourceFileLoader(
        "lldap_create_user",
        str(
            SALTSTACK_DIRECTORY
            / "states/roles/kam-classroom/files/lldap_create_user.py"
        ),
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise AssertionError("Could not load lldap-create-user script")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_argument_parser_accepts_missing_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that email is optional for account creation."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lldap-create-user",
            "alice",
        ],
    )

    script = _load_script()
    monkeypatch.setattr(script.socket, "getfqdn", lambda: "genesis.meh.gripe")

    arguments = script.parse_arguments()

    assert arguments.email is None
    assert arguments.email_domain == "genesis.meh.gripe"
    assert arguments.uid_number is None
    assert arguments.gid_number is None
    assert arguments.group == "humans"
    assert arguments.secondary_group_names == []
    assert arguments.forgejo_url == "http://127.0.0.1:3000/"
    assert arguments.forgejo_binary == "/usr/local/bin/forgejo"
    assert arguments.forgejo_configuration_file == "/etc/forgejo/app.ini"
    assert arguments.forgejo_work_path == "/data/forgejo"
    assert arguments.forgejo_run_user == "git"
    assert arguments.home_quota_command == "/usr/local/sbin/apply-user-quotas"
    assert arguments.home_quota_configuration_file == "/etc/quotas/user-quotas.json"
    assert arguments.pwscore_command == "/usr/bin/pwscore"
    assert arguments.print_user_id_number is False


def test_build_user_input_defaults_email_when_missing() -> None:
    """Test that GraphQL input includes a generated email when none is provided."""
    arguments = argparse.Namespace(
        username="alice",
        email=None,
        email_domain="genesis.meh.gripe",
        display_name=None,
        uid_number=20001,
        gid_number=20000,
        home_directory=None,
        shell="/bin/bash",
    )

    assert _load_script().build_user_input(arguments, 10001, 1000) == {
        "id": "alice",
        "email": "alice@genesis.meh.gripe",
        "displayName": "alice",
        "attributes": [
            {"name": "uidNumber", "value": ["10001"]},
            {"name": "gidNumber", "value": ["1000"]},
            {"name": "homeDirectory", "value": ["/home/alice"]},
            {"name": "unixShell", "value": ["/bin/bash"]},
        ],
    }


def test_resolve_secondary_group_names_includes_default_groups() -> None:
    """Test that new users are added to the classroom default secondary groups."""
    arguments = argparse.Namespace(group="humans", secondary_group_names=[])

    assert _load_script().resolve_secondary_group_names(arguments) == [
        "linux-foundations",
    ]


def test_resolve_secondary_group_names_deduplicates_and_excludes_primary() -> None:
    """Test that primary and duplicate secondary groups are filtered."""
    arguments = argparse.Namespace(
        group="linux-foundations",
        secondary_group_names=["makers", "linux-foundations", "makers"],
    )

    assert _load_script().resolve_secondary_group_names(arguments) == [
        "makers",
    ]


def test_build_user_input_includes_email_when_provided() -> None:
    """Test that GraphQL input includes email when one is provided."""
    arguments = argparse.Namespace(
        username="alice",
        email="alice@example.org",
        display_name="Alice",
        uid_number=20001,
        gid_number=20000,
        home_directory="/srv/alice",
        shell="/bin/zsh",
    )

    assert _load_script().build_user_input(arguments, 20001, 20000) == {
        "id": "alice",
        "email": "alice@example.org",
        "displayName": "Alice",
        "attributes": [
            {"name": "uidNumber", "value": ["20001"]},
            {"name": "gidNumber", "value": ["20000"]},
            {"name": "homeDirectory", "value": ["/srv/alice"]},
            {"name": "unixShell", "value": ["/bin/zsh"]},
        ],
    }


def test_ensure_student_ssh_key_creates_keypair(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Test that account creation prepares an SSH key in the student home."""
    script = _load_script()
    chown_calls: list[tuple[str, int, int]] = []
    chmod_calls: list[tuple[str, int]] = []
    run_calls: list[list[str]] = []

    def chown(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        user_id: int,
        group_id: int,
    ) -> None:
        chown_calls.append((str(path), user_id, group_id))

    def chmod(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes], mode: int
    ) -> None:
        chmod_calls.append((str(path), mode))

    def run(arguments: list[str], *, check: bool) -> subprocess.CompletedProcess[str]:
        run_calls.append(arguments)
        assert check is True
        _ = Path(arguments[-1]).write_text("private key\n", encoding="utf-8")
        _ = Path(arguments[-1] + ".pub").write_text(
            "ssh-ed25519 public-key\n", encoding="utf-8"
        )
        return subprocess.CompletedProcess(arguments, 0)

    monkeypatch.setattr(script.os, "chown", chown)
    monkeypatch.setattr(script.os, "chmod", chmod)
    monkeypatch.setattr(script.subprocess, "run", run)

    assert (
        script.ensure_student_ssh_key(
            str(tmp_path / "alice"),
            10001,
            1001,
            "alice@genesis.meh.gripe",
        )
        == "ssh-ed25519 public-key"
    )
    assert run_calls == [
        [
            "/usr/bin/ssh-keygen",
            "-q",
            "-t",
            "ed25519",
            "-N",
            "",
            "-C",
            "alice@genesis.meh.gripe",
            "-f",
            str(tmp_path / "alice/.ssh/id_ed25519"),
        ]
    ]
    assert chown_calls == [
        (str(tmp_path / "alice"), 10001, 1001),
        (str(tmp_path / "alice/.ssh"), 10001, 1001),
        (str(tmp_path / "alice/.ssh/id_ed25519"), 10001, 1001),
        (str(tmp_path / "alice/.ssh/id_ed25519.pub"), 10001, 1001),
    ]
    assert chmod_calls == [
        (str(tmp_path / "alice"), 0o711),
        (str(tmp_path / "alice/.ssh"), 0o700),
        (str(tmp_path / "alice/.ssh/id_ed25519"), 0o600),
        (str(tmp_path / "alice/.ssh/id_ed25519.pub"), 0o644),
    ]


def test_ensure_student_home_creates_bin_and_git_identity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """New learners receive the shell and Git prerequisites for their first site build."""
    script = _load_script()
    chown_calls: list[tuple[str, int, int]] = []

    def chown(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        user_id: int,
        group_id: int,
    ) -> None:
        chown_calls.append((str(path), user_id, group_id))

    monkeypatch.setattr(script.os, "chown", chown)

    script.ensure_student_home(
        str(tmp_path / "alice"),
        10001,
        1001,
        "alice",
        "alice@example.org",
    )

    assert (tmp_path / "alice/bin").is_dir()
    assert (tmp_path / "alice/public_html").is_dir()
    assert (tmp_path / "alice").stat().st_mode & 0o777 == 0o711
    assert (tmp_path / "alice/public_html").stat().st_mode & 0o777 == 0o755
    assert (tmp_path / "alice/.gitconfig").read_text(encoding="utf-8") == (
        "[user]\n\tname = alice\n\temail = alice@example.org\n"
    )
    assert chown_calls == [
        (str(tmp_path / "alice"), 10001, 1001),
        (str(tmp_path / "alice/bin"), 10001, 1001),
        (str(tmp_path / "alice/public_html"), 10001, 1001),
        (str(tmp_path / "alice/.gitconfig"), 10001, 1001),
    ]


def test_create_forgejo_user_runs_forgejo_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that Forgejo account creation uses the Forgejo admin CLI."""
    script = _load_script()
    calls: list[list[str]] = []
    arguments = argparse.Namespace(
        username="alice",
        email=None,
        email_domain="genesis.meh.gripe",
        display_name="Alice",
        forgejo_run_user="git",
        forgejo_binary="/usr/local/bin/forgejo",
        forgejo_configuration_file="/etc/forgejo/app.ini",
        forgejo_work_path="/data/forgejo",
    )

    def run_forgejo_command(
        command_arguments: argparse.Namespace,
        command: list[str],
    ) -> str:
        assert command_arguments == arguments
        calls.append(command)
        return "created\n"

    monkeypatch.setattr(script, "run_forgejo_command", run_forgejo_command)

    script.create_forgejo_user(arguments, "forgejo-password")

    assert calls == [
        [
            "admin",
            "user",
            "create",
            "--username",
            "alice",
            "--email",
            "alice@genesis.meh.gripe",
            "--password",
            "forgejo-password",
            "--must-change-password=false",
            "--fullname",
            "Alice",
        ]
    ]


def test_create_forgejo_user_ignores_existing_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that pre-existing Forgejo users are accepted for account linking."""
    script = _load_script()

    def run_forgejo_command(
        command_arguments: argparse.Namespace,
        command: list[str],
    ) -> str:
        assert command_arguments.username == "alice"
        assert command[0:3] == ["admin", "user", "create"]
        raise script.ForgejoError("CreateUser: user already exists")

    monkeypatch.setattr(script, "run_forgejo_command", run_forgejo_command)

    script.create_forgejo_user(
        argparse.Namespace(
            username="alice",
            email=None,
            email_domain="genesis.meh.gripe",
            display_name=None,
        ),
        "forgejo-password",
    )


def test_change_forgejo_password_runs_forgejo_cli(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that Forgejo local passwords are reset for API provisioning."""
    script = _load_script()
    calls: list[list[str]] = []
    arguments = argparse.Namespace(username="alice")

    def run_forgejo_command(
        command_arguments: argparse.Namespace,
        command: list[str],
    ) -> str:
        assert command_arguments == arguments
        calls.append(command)
        return "token-value\n"

    monkeypatch.setattr(script, "run_forgejo_command", run_forgejo_command)

    script.change_forgejo_password(arguments, "forgejo-password")

    assert calls == [
        [
            "admin",
            "user",
            "change-password",
            "--username",
            "alice",
            "--password",
            "forgejo-password",
            "--must-change-password=false",
        ]
    ]


def test_forgejo_basic_authorization_encodes_password() -> None:
    """Test that API provisioning uses Basic auth without persistent tokens."""
    assert (
        _load_script().forgejo_basic_authorization("alice", "forgejo-password")
        == "Basic YWxpY2U6Zm9yZ2Vqby1wYXNzd29yZA=="
    )


def test_ensure_forgejo_public_key_adds_missing_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that the Forgejo user credentials install the generated SSH public key."""
    script = _load_script()
    calls: list[tuple[str, str, str, dict[str, object] | None]] = []
    arguments = argparse.Namespace(
        forgejo_url="http://127.0.0.1:3000/",
        username="alice",
        email=None,
        email_domain="genesis.meh.gripe",
    )

    def forgejo_json_request(
        url: str,
        method: str,
        authorization: str,
        payload: dict[str, object] | None = None,
    ) -> object:
        calls.append((url, method, authorization, payload))
        if method == "GET":
            return [{"key": "ssh-ed25519 existing"}]
        return {"id": 1}

    monkeypatch.setattr(script, "forgejo_json_request", forgejo_json_request)

    script.ensure_forgejo_public_key(
        arguments, "Basic authorization", "ssh-ed25519 generated"
    )

    assert calls == [
        (
            "http://127.0.0.1:3000/api/v1/user/keys",
            "GET",
            "Basic authorization",
            None,
        ),
        (
            "http://127.0.0.1:3000/api/v1/user/keys",
            "POST",
            "Basic authorization",
            {
                "title": "alice@genesis.meh.gripe",
                "key": "ssh-ed25519 generated",
            },
        ),
    ]


def test_provision_forgejo_account_creates_account_and_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that Forgejo provisioning does not create persistent API tokens."""
    script = _load_script()
    calls: list[tuple[str, object]] = []
    arguments = argparse.Namespace(username="alice")

    def create_forgejo_user(
        command_arguments: argparse.Namespace,
        forgejo_password: str,
    ) -> None:
        calls.append(("create_forgejo_user", (command_arguments, forgejo_password)))

    def change_forgejo_password(
        command_arguments: argparse.Namespace,
        forgejo_password: str,
    ) -> None:
        calls.append(("change_forgejo_password", (command_arguments, forgejo_password)))

    def ensure_forgejo_public_key(
        command_arguments: argparse.Namespace,
        authorization: str,
        public_key: str,
    ) -> None:
        calls.append(
            (
                "ensure_forgejo_public_key",
                (command_arguments, authorization, public_key),
            )
        )

    monkeypatch.setattr(script, "create_forgejo_user", create_forgejo_user)
    monkeypatch.setattr(script, "change_forgejo_password", change_forgejo_password)
    monkeypatch.setattr(script, "ensure_forgejo_public_key", ensure_forgejo_public_key)

    script.provision_forgejo_account(arguments, "forgejo-password", "public-key")

    assert calls == [
        ("create_forgejo_user", (arguments, "forgejo-password")),
        ("change_forgejo_password", (arguments, "forgejo-password")),
        (
            "ensure_forgejo_public_key",
            (
                arguments,
                "Basic YWxpY2U6Zm9yZ2Vqby1wYXNzd29yZA==",
                "public-key",
            ),
        ),
    ]


def test_apply_home_quota_runs_quota_helper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that account creation applies the classroom default home quota."""
    script = _load_script()
    calls: list[list[str]] = []

    def run(
        arguments: list[str],
        *,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(arguments)
        assert check is True
        return subprocess.CompletedProcess(arguments, 0)

    monkeypatch.setattr(script.subprocess, "run", run)

    script.apply_home_quota(
        "/usr/local/sbin/apply-user-quotas",
        "/etc/quotas/user-quotas.json",
        "alice",
        10001,
        ["humans", "linux-foundations"],
    )

    assert calls == [
        [
            "/usr/local/sbin/apply-user-quotas",
            "--configuration",
            "/etc/quotas/user-quotas.json",
            "--username",
            "alice",
            "--user-id-number",
            "10001",
            "--group",
            "humans",
            "--group",
            "linux-foundations",
        ]
    ]


def test_set_password_discards_lldap_helper_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The UID-only output mode is not mixed with LLDAP password status output."""
    script = _load_script()

    def run(
        arguments: list[str],
        *,
        env: dict[str, str],
        check: bool,
        stdout: int,
    ) -> subprocess.CompletedProcess[str]:
        assert arguments[0] == "/usr/local/bin/lldap_set_password"
        assert env["LLDAP_USER_PASSWORD"] == "secret"
        assert check is True
        assert stdout == subprocess.DEVNULL
        return subprocess.CompletedProcess(arguments, 0)

    monkeypatch.setattr(script.subprocess, "run", run)

    script.set_password("http://127.0.0.1:17170/", "token", "alice", "secret")


def test_allocate_user_id_number_uses_highest_existing_uid_plus_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that automatic uidNumber allocation uses the highest used value."""
    script = _load_script()

    def load_users(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return [
            {
                "id": "alice",
                "attributes": [{"name": "uidnumber", "value": ["20000"]}],
            },
            {
                "id": "bob",
                "attributes": [{"name": "uidnumber", "value": ["20003"]}],
            },
            {
                "id": "charlie",
                "attributes": [{"name": "uidnumber", "value": ["20100"]}],
            },
            {
                "id": "system",
                "attributes": [{"name": "uidnumber", "value": ["999"]}],
            },
        ]

    monkeypatch.setattr(script, "load_users", load_users)

    assert script.allocate_user_id_number("http://127.0.0.1:17170/", "token") == 20101


def test_allocate_user_id_number_defaults_to_20000_when_range_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that automatic uidNumber allocation starts at 20000."""
    script = _load_script()

    def load_users(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return [
            {
                "id": "system",
                "attributes": [{"name": "uidnumber", "value": ["999"]}],
            }
        ]

    monkeypatch.setattr(script, "load_users", load_users)

    assert script.allocate_user_id_number("http://127.0.0.1:17170/", "token") == 20000


def test_allocate_user_id_number_rejects_an_exhausted_range(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that automatic uidNumber allocation stops at 20999."""
    script = _load_script()

    def load_users(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return [
            {
                "id": "alice",
                "attributes": [{"name": "uidnumber", "value": ["20999"]}],
            }
        ]

    monkeypatch.setattr(script, "load_users", load_users)

    with pytest.raises(script.LldapError) as error:
        script.allocate_user_id_number("http://127.0.0.1:17170/", "token")

    assert str(error.value) == "No uidNumber is available in 20000-20999"


def test_ensure_user_id_number_available_rejects_duplicate_uid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that explicit uidNumber assignment cannot reuse an existing value."""
    script = _load_script()

    def load_users(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return [
            {
                "id": "alice",
                "attributes": [{"name": "uidnumber", "value": ["10000"]}],
            }
        ]

    monkeypatch.setattr(script, "load_users", load_users)

    with pytest.raises(script.LldapError) as error:
        script.ensure_user_id_number_available(
            "http://127.0.0.1:17170/",
            "token",
            10000,
        )

    assert str(error.value) == "uidNumber 10000 is already used by alice"


def test_ensure_email_available_rejects_case_insensitive_duplicate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Email uniqueness matches LLDAP's lowercase-email constraint."""
    script = _load_script()

    def load_users(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return [
            {
                "id": "alice",
                "email": "Alice@Example.org",
                "attributes": [],
            }
        ]

    monkeypatch.setattr(script, "load_users", load_users)

    with pytest.raises(script.LldapError) as error:
        script.ensure_email_available(
            "http://127.0.0.1:17170/", "token", "alice@example.org"
        )

    assert str(error.value) == "An account already uses that email address."


def test_generate_password_uses_debian_diceware(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that generated passwords come from the Debian diceware package."""
    script = _load_script()
    calls: list[list[str]] = []

    def run(
        arguments: list[str],
        *,
        check: bool,
        stdout: int,
        stderr: int,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        calls.append(arguments)
        assert check is True
        assert stdout == subprocess.PIPE
        assert stderr == subprocess.PIPE
        assert text is True
        return subprocess.CompletedProcess(
            arguments,
            0,
            stdout="alpha-bravo-charlie-delta-echo-foxtrot\n",
            stderr="",
        )

    monkeypatch.setattr(script.subprocess, "run", run)

    assert script.generate_password() == "alpha-bravo-charlie-delta-echo-foxtrot"
    assert calls == [
        ["/usr/bin/diceware", "--no-caps", "--delimiter", "-", "--num", "6"]
    ]


def test_password_strength_uses_pwscore(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that initial passwords are checked by libpwquality."""
    script = _load_script()
    calls: list[dict[str, object]] = []

    def run(
        arguments: list[str],
        *,
        check: bool,
        input: str,
        stdout: int,
        stderr: int,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        calls.append({"arguments": arguments, "input": input})
        assert check is False
        assert stdout == subprocess.PIPE
        assert stderr == subprocess.PIPE
        assert text is True
        return subprocess.CompletedProcess(arguments, 1, stdout="", stderr="too weak\n")

    monkeypatch.setattr(script.subprocess, "run", run)

    assert (
        script.password_strength_error(
            "/usr/bin/pwscore",
            "alice",
            "short",
        )
        == "too weak"
    )
    assert calls == [{"arguments": ["/usr/bin/pwscore"], "input": "short\n"}]


def test_resolve_password_rejects_username_derived_stdin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that admin-provided initial passwords cannot contain the username."""
    script = _load_script()
    monkeypatch.setattr(sys, "stdin", io.StringIO("prefix-alice-suffix\n"))

    with pytest.raises(script.LldapError) as error:
        script.resolve_password("/usr/bin/pwscore", "alice", True)

    assert str(error.value) == "Password rejected: It contains the username."


def test_generate_compliant_password_retries_after_pwquality_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that generated initial passwords are checked before use."""
    script = _load_script()
    generated_passwords = iter(["weak-password", "strong-password"])
    checked_passwords: list[str] = []

    monkeypatch.setattr(script, "generate_password", lambda: next(generated_passwords))

    def password_strength_error(
        pwscore_command: str,
        username: str,
        password: str,
    ) -> str | None:
        assert pwscore_command == "/usr/bin/pwscore"
        assert username == "alice"
        checked_passwords.append(password)
        if password == "weak-password":
            return "too weak"
        return None

    monkeypatch.setattr(script, "password_strength_error", password_strength_error)

    assert (
        script.generate_compliant_password("/usr/bin/pwscore", "alice")
        == "strong-password"
    )
    assert checked_passwords == ["weak-password", "strong-password"]


def test_ensure_schema_ignores_duplicate_schema_attribute_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that schema creation tolerates attributes created by an earlier run."""
    script = _load_script()
    calls: list[dict[str, object]] = []

    def load_schema(base_url: str, token: str) -> dict[str, object]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return {
            "userSchema": {
                "attributes": [],
                "ldapObjectClasses": [{"objectClass": "posixAccount"}],
            },
            "groupSchema": {"attributes": [{"name": "gidNumber"}]},
        }

    def graphql(
        base_url: str,
        token: str,
        query: str,
        variables: dict[str, object],
    ) -> dict[str, object]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        assert "addUserAttribute" in query
        calls.append(variables)
        raise script.LldapError(
            "UNIQUE constraint failed: user_attribute_schema.user_attribute_schema_name"
        )

    monkeypatch.setattr(script, "load_schema", load_schema)
    monkeypatch.setattr(script, "graphql", graphql)

    script.ensure_schema("http://127.0.0.1:17170/", "token")

    assert calls == [
        {
            "name": "uidNumber",
            "attributeType": "INTEGER",
            "isList": False,
            "isVisible": True,
            "isEditable": False,
        },
        {
            "name": "gidNumber",
            "attributeType": "INTEGER",
            "isList": False,
            "isVisible": True,
            "isEditable": False,
        },
        {
            "name": "homeDirectory",
            "attributeType": "STRING",
            "isList": False,
            "isVisible": True,
            "isEditable": False,
        },
        {
            "name": "unixShell",
            "attributeType": "STRING",
            "isList": False,
            "isVisible": True,
            "isEditable": False,
        },
        {
            "name": "sshPublicKey",
            "attributeType": "STRING",
            "isList": True,
            "isVisible": True,
            "isEditable": True,
        },
    ]


def test_ensure_group_uses_existing_gid_when_gid_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that an existing group supplies the default gidNumber."""
    script = _load_script()

    def load_groups(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return [
            {
                "id": 42,
                "displayName": "humans",
                "attributes": [{"name": "gidnumber", "value": ["20000"]}],
            }
        ]

    monkeypatch.setattr(script, "load_groups", load_groups)

    assert script.ensure_group("http://127.0.0.1:17170/", "token", "humans", None) == (
        42,
        20000,
    )


def test_ensure_group_rejects_group_without_gid_number(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that account creation does not patch group attributes."""
    script = _load_script()

    def load_groups(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return [{"id": 42, "displayName": "humans", "attributes": []}]

    monkeypatch.setattr(script, "load_groups", load_groups)

    with pytest.raises(script.LldapError) as error:
        script.ensure_group("http://127.0.0.1:17170/", "token", "humans", None)

    assert (
        str(error.value)
        == "Group humans does not define gidNumber; run Salt to prepare managed groups"
    )


def test_ensure_group_rejects_missing_group(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that account creation does not create missing groups."""
    script = _load_script()

    def load_groups(base_url: str, token: str) -> list[dict[str, object]]:
        assert base_url == "http://127.0.0.1:17170/"
        assert token == "token"
        return []

    monkeypatch.setattr(script, "load_groups", load_groups)

    with pytest.raises(script.LldapError) as error:
        script.ensure_group("http://127.0.0.1:17170/", "token", "humans", None)

    assert str(error.value) == "Group humans does not exist; run Salt to create it"


def test_main_continues_when_sss_cache_invalidation_fails(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test that an SSSD failure does not fail account creation."""
    script = _load_script()
    calls: list[str] = []
    arguments = argparse.Namespace(
        environment_file="/etc/lldap.env",
        pwscore_command="/usr/bin/pwscore",
        username="alice",
        base_url="http://127.0.0.1:17170/",
        admin_username="admin",
        group="humans",
        gid_number=None,
        uid_number=20000,
        home_directory="/home/alice",
        email="alice@example.org",
        home_quota_command="/usr/local/sbin/apply-user-quotas",
        home_quota_configuration_file="/etc/quotas/user-quotas.json",
        print_user_id_number=False,
        password_stdin=True,
    )

    monkeypatch.setattr(script, "parse_arguments", lambda: arguments)
    monkeypatch.setattr(
        script,
        "read_environment_file",
        lambda environment_file: {"LLDAP_LDAP_USER_PASS": "admin-secret"},
    )
    monkeypatch.setattr(
        script,
        "resolve_password",
        lambda pwscore_command, username, password_stdin: "learner-secret",
    )
    monkeypatch.setattr(
        script,
        "login",
        lambda base_url, username, password: "token",
    )
    monkeypatch.setattr(script, "ensure_schema", lambda base_url, token: None)
    monkeypatch.setattr(
        script,
        "ensure_group",
        lambda base_url, token, group_name, group_id_number: (20000, 20000),
    )
    monkeypatch.setattr(
        script,
        "resolve_secondary_group_names",
        lambda parsed_arguments: ["linux-foundations"],
    )
    monkeypatch.setattr(
        script,
        "ensure_user_id_number_available",
        lambda base_url, token, user_id_number: None,
    )
    monkeypatch.setattr(
        script,
        "ensure_email_available",
        lambda base_url, token, email: None,
    )
    monkeypatch.setattr(
        script,
        "ensure_student_home",
        lambda home_directory, user_id_number, group_id_number, username, email: None,
    )
    monkeypatch.setattr(
        script,
        "ensure_student_ssh_key",
        lambda home_directory, user_id_number, group_id_number, email: "public-key",
    )
    monkeypatch.setattr(
        script,
        "create_user",
        lambda parsed_arguments, base_url, token, user_id_number, group_id_number: None,
    )
    monkeypatch.setattr(
        script,
        "add_user_to_group",
        lambda base_url, token, username, group_identifier: None,
    )
    monkeypatch.setattr(
        script,
        "apply_home_quota",
        lambda quota_command, quota_configuration_file, username, user_id_number, group_names: (
            None
        ),
    )
    monkeypatch.setattr(
        script,
        "set_password",
        lambda base_url, token, username, password: calls.append("password"),
    )

    def invalidate_sss_cache(username: str) -> None:
        raise subprocess.CalledProcessError(
            1,
            ["/usr/sbin/sss_cache", "-u", username],
            stderr="cache unavailable",
        )

    monkeypatch.setattr(script, "invalidate_sss_cache", invalidate_sss_cache)
    monkeypatch.setattr(
        script,
        "provision_forgejo_account",
        lambda parsed_arguments, password, public_key: calls.append("forgejo"),
    )
    monkeypatch.setattr(script, "generate_password", lambda: "forgejo-secret")

    assert script.main() == 0
    assert calls == ["password", "forgejo"]
    assert capsys.readouterr().err == (
        "lldap-create-user: could not invalidate SSSD cache for alice: "
        "cache unavailable\n"
    )
