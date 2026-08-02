"""Tests for configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from maker_guide.config import (
    ConfigError,
    load_config,
    load_database_path,
    load_llm_tutor_config,
    load_unix_groups_config,
)
from maker_guide.llm_tutor import DEFAULT_TUTOR_MODEL


def test_load_database_path_does_not_require_irc_secret(
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Migration commands can read the database path without IRC credentials."""
    monkeypatch.delenv("MAKER_GUIDE_IRC_PASSWORD", raising=False)
    database_path = temporary_path / "state.db"

    assert (
        load_database_path(_write_database_only_config(temporary_path, database_path))
        == database_path
    )


def test_load_config_includes_database_path(temporary_path: Path) -> None:
    """The full daemon config includes the SQLite database path."""
    database_path = temporary_path / "state.db"

    assert (
        load_config(_write_full_config(temporary_path, database_path)).database.path
        == database_path
    )


def test_load_config_reads_irc_chat_limits(temporary_path: Path) -> None:
    """IRC chat workers and queue size are bounded by operator config."""
    configuration = load_config(_write_full_config(temporary_path, temporary_path / "state.db"))

    assert configuration.irc.chat_worker_count == 2
    assert configuration.irc.chat_queue_size == 50


@pytest.mark.parametrize("config_line", ["chat_worker_count = 0", "chat_queue_size = 0"])
def test_load_config_rejects_non_positive_irc_chat_limits(
    temporary_path: Path,
    config_line: str,
) -> None:
    """IRC chat worker limits must be positive to preserve bounded processing."""
    password_path = temporary_path / "irc-password.txt"
    password_path.write_text("secret", encoding="utf-8")
    configuration_path = temporary_path / "bad-irc-limits.toml"
    configuration_path.write_text(
        f"""
        [database]
        path = "{temporary_path / "state.db"}"

        [socket]
        path = "{temporary_path / "maker-guide.sock"}"

        [irc]
        server = "irc.example"
        nickname = "guide"
        username = "guide"
        channels = ["#kolam"]
        {config_line}

        [irc.sasl]
        username = "guide"
        password_file = "{password_path}"
        """,
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="must be positive"):
        load_config(configuration_path)


@pytest.mark.parametrize(
    ("section", "config_line", "error_pattern"),
    [
        ("socket", "backlog = 0", "backlog must be positive"),
        ("socket", "max_line_bytes = 0", "max_line_bytes must be positive"),
        ("socket", "read_timeout_seconds = 0", "read_timeout_seconds must be positive"),
        ("socket", "queue_size = 0", "queue_size must be positive"),
        ("socket", "mode = -1", "mode must be between 0 and 0o777"),
        ("socket", "mode = 512", "mode must be between 0 and 0o777"),
        ("socket", "allowed_user_ids = [true]", "allowed_user_ids must be a list"),
        ("socket", "allowed_user_ids = [-1]", "allowed_user_ids must be a list"),
        ("irc", "port = 0", "port must be between 1 and 65535"),
        ("irc", "port = 65536", "port must be between 1 and 65535"),
        ("irc", "connect_timeout_seconds = 0", "connect_timeout_seconds must be positive"),
        (
            "irc",
            "registration_timeout_seconds = 0",
            "registration_timeout_seconds must be positive",
        ),
        ("irc", "read_timeout_seconds = 0", "read_timeout_seconds must be positive"),
        ("irc", "reconnect_initial_seconds = 0", "reconnect_initial_seconds must be positive"),
        ("irc", "reconnect_max_seconds = 0", "reconnect_max_seconds must be positive"),
        ("irc", "outbound_queue_size = 0", "outbound_queue_size must be positive"),
        ("irc", "outbound_interval_seconds = 0", "outbound_interval_seconds must be positive"),
    ],
)
def test_load_config_rejects_invalid_numeric_values(
    temporary_path: Path,
    section: str,
    config_line: str,
    error_pattern: str,
) -> None:
    """Daemon config rejects invalid numeric values at operator load time."""
    with pytest.raises(ConfigError, match=error_pattern):
        load_config(_write_full_config_with_extra_line(temporary_path, section, config_line))


@pytest.mark.parametrize(
    ("config_line", "error_pattern"),
    [
        ("timeout_seconds = 0", "timeout_seconds must be positive"),
        ("max_tokens = 0", "max_tokens must be positive"),
        ("rate_limit_per_minute = 0", "rate_limit_per_minute must be positive"),
    ],
)
def test_load_llm_tutor_config_rejects_invalid_numeric_values(
    temporary_path: Path,
    config_line: str,
    error_pattern: str,
) -> None:
    """LLM tutor numeric limits fail fast with clear errors."""
    configuration_path = temporary_path / "bad-llm-numeric.toml"
    api_key_path = temporary_path / "openrouter-api-key"
    api_key_path.write_text("sk-or-test\n", encoding="utf-8")
    configuration_path.write_text(
        f"""
        [llm_tutor]
        enabled = true
        api_key_file = "{api_key_path}"
        {config_line}
        """,
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match=error_pattern):
        load_llm_tutor_config(configuration_path)


def test_load_llm_tutor_config_uses_deepseek_flash_default_model(
    temporary_path: Path,
) -> None:
    """LLM config reads provider secrets from a configured file."""
    tutor_configuration = load_llm_tutor_config(_write_llm_tutor_config(temporary_path))

    assert tutor_configuration is not None
    assert tutor_configuration.provider == "openrouter"
    assert tutor_configuration.model == DEFAULT_TUTOR_MODEL
    assert tutor_configuration.api_key == "sk-or-test"
    assert tutor_configuration.max_tokens == 1200


def test_load_llm_tutor_config_rejects_unknown_provider(temporary_path: Path) -> None:
    """Only the OpenRouter provider is supported for now."""
    configuration_path = temporary_path / "bad-llm.toml"
    configuration_path.write_text(
        """
        [llm_tutor]
        enabled = true
        provider = "other"
        """,
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="provider must be openrouter"):
        load_llm_tutor_config(configuration_path)


def test_load_unix_groups_config_reads_commands_without_irc_secret(
    temporary_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Group sync config does not require IRC credentials."""
    monkeypatch.delenv("MAKER_GUIDE_IRC_PASSWORD", raising=False)
    configuration_path = temporary_path / "groups.toml"
    configuration_path.write_text(
        f"""
        [unix_groups]
        enabled = true
        grant_command = ["sudo", "-n", "{temporary_path / "grant"}"]
        revoke_command = ["sudo", "-n", "{temporary_path / "revoke"}"]
        managed_groups = ["lf2607"]
        """,
        encoding="utf-8",
    )

    unix_groups_configuration = load_unix_groups_config(configuration_path)

    assert unix_groups_configuration is not None
    assert unix_groups_configuration.grant_command == (
        "sudo",
        "-n",
        str(temporary_path / "grant"),
    )
    assert unix_groups_configuration.revoke_command == (
        "sudo",
        "-n",
        str(temporary_path / "revoke"),
    )
    assert unix_groups_configuration.managed_groups == frozenset({"lf2607"})


def test_load_unix_groups_config_rejects_missing_command(temporary_path: Path) -> None:
    """Enabled Unix group sync requires both mutation commands."""
    configuration_path = temporary_path / "bad-groups.toml"
    configuration_path.write_text(
        """
        [unix_groups]
        enabled = true
        grant_command = ["sudo", "-n", "/usr/local/sbin/maker-guide-grant-group"]
        managed_groups = ["lf2607"]
        """,
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match=r"unix_groups\.revoke_command is required"):
        load_unix_groups_config(configuration_path)


@pytest.mark.parametrize(
    ("managed_groups_line", "error_pattern"),
    [
        ("", r"unix_groups\.managed_groups is required"),
        ("managed_groups = []", r"unix_groups\.managed_groups must not be empty"),
        (
            'managed_groups = ["lf2607", "lf2607"]',
            r"unix_groups\.managed_groups must not contain duplicates",
        ),
        (
            'managed_groups = ["sudo"]',
            r"unix_groups\.managed_groups contains unsafe Unix group: sudo",
        ),
    ],
)
def test_load_unix_groups_config_rejects_bad_managed_groups(
    temporary_path: Path,
    managed_groups_line: str,
    error_pattern: str,
) -> None:
    """Enabled Unix group sync requires an explicit safe allowlist."""
    configuration_path = temporary_path / "bad-managed-groups.toml"
    configuration_path.write_text(
        f"""
        [unix_groups]
        enabled = true
        grant_command = ["sudo", "-n", "/usr/local/sbin/maker-guide-grant-group"]
        revoke_command = ["sudo", "-n", "/usr/local/sbin/maker-guide-revoke-group"]
        {managed_groups_line}
        """,
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match=error_pattern):
        load_unix_groups_config(configuration_path)


def test_load_database_path_requires_database_table(temporary_path: Path) -> None:
    """Database path loading fails loudly when the table is missing."""
    configuration_path = temporary_path / "config.toml"
    configuration_path.write_text("", encoding="utf-8")

    with pytest.raises(ConfigError, match=r"root\.database is required"):
        load_database_path(configuration_path)


def _write_database_only_config(temporary_path: Path, database_path: Path) -> Path:
    configuration_path = temporary_path / "database-only.toml"
    configuration_path.write_text(
        f"""
        [database]
        path = "{database_path}"

        [irc]
        nickname = "guide"

        [irc.sasl]
        password_env = "MAKER_GUIDE_IRC_PASSWORD"
        """,
        encoding="utf-8",
    )
    return configuration_path


def _write_full_config(temporary_path: Path, database_path: Path) -> Path:
    password_path = temporary_path / "irc-password.txt"
    password_path.write_text("secret", encoding="utf-8")
    configuration_path = temporary_path / "config.toml"
    configuration_path.write_text(
        f"""
        [database]
        path = "{database_path}"

        [socket]
        path = "{temporary_path / "maker-guide.sock"}"

        [irc]
        server = "irc.example"
        nickname = "guide"
        username = "guide"
        channels = ["#kolam"]
        chat_worker_count = 2
        chat_queue_size = 50

        [irc.sasl]
        username = "guide"
        password_file = "{password_path}"
        """,
        encoding="utf-8",
    )
    return configuration_path


def _write_full_config_with_extra_line(
    temporary_path: Path,
    section: str,
    config_line: str,
) -> Path:
    password_path = temporary_path / "irc-password.txt"
    password_path.write_text("secret", encoding="utf-8")
    socket_extra_line = config_line if section == "socket" else ""
    irc_extra_line = config_line if section == "irc" else ""
    configuration_path = temporary_path / "bad-numeric.toml"
    configuration_path.write_text(
        f"""
        [database]
        path = "{temporary_path / "state.db"}"

        [socket]
        path = "{temporary_path / "maker-guide.sock"}"
        {socket_extra_line}

        [irc]
        server = "irc.example"
        nickname = "guide"
        username = "guide"
        channels = ["#kolam"]
        {irc_extra_line}

        [irc.sasl]
        username = "guide"
        password_file = "{password_path}"
        """,
        encoding="utf-8",
    )
    return configuration_path


def _write_llm_tutor_config(temporary_path: Path) -> Path:
    configuration_path = temporary_path / "llm.toml"
    api_key_path = temporary_path / "openrouter-api-key"
    api_key_path.write_text("sk-or-test\n", encoding="utf-8")
    configuration_path.write_text(
        f"""
        [llm_tutor]
        enabled = true
        api_key_file = "{api_key_path}"
        """,
        encoding="utf-8",
    )
    return configuration_path
