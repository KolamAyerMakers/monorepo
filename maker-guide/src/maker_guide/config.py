"""Configuration loading for the bot daemon."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Never, cast

from maker_guide.llm_tutor import (
    DEFAULT_TUTOR_MAX_TOKENS,
    DEFAULT_TUTOR_MODEL,
    DEFAULT_TUTOR_RATE_LIMIT_PER_MINUTE,
    DEFAULT_TUTOR_TIMEOUT_SECONDS,
)
from maker_guide.unix_names import is_allowed_managed_group_name

DEFAULT_CONFIG_PATH = Path("/etc/maker-guide/config.toml")


class ConfigError(ValueError):
    """Raised when configuration is missing or invalid."""


@dataclass(frozen=True, kw_only=True, slots=True)
class SocketConfig:
    """Unix socket listener configuration."""

    path: Path
    mode: int = 0o666
    allowed_group: str | None = None
    allowed_user_ids: frozenset[int] = frozenset()
    backlog: int = 100
    max_line_bytes: int = 16_384
    read_timeout_seconds: float = 0.25
    queue_size: int = 1_000


@dataclass(frozen=True, kw_only=True, slots=True)
class SaslConfig:
    """IRC SASL configuration."""

    username: str
    password: str
    mechanism: str = "PLAIN"


@dataclass(frozen=True, kw_only=True, slots=True)
class IrcConfig:
    """IRC connection configuration."""

    server: str
    port: int
    nickname: str
    username: str
    realname: str
    channels: tuple[str, ...]
    sasl: SaslConfig
    tls: bool = True
    connect_timeout_seconds: float = 10.0
    registration_timeout_seconds: float = 10.0
    read_timeout_seconds: float = 300.0
    reconnect_initial_seconds: float = 1.0
    reconnect_max_seconds: float = 60.0
    outbound_queue_size: int = 200
    outbound_interval_seconds: float = 1.5
    chat_worker_count: int = 1
    chat_queue_size: int = 100


@dataclass(frozen=True, kw_only=True, slots=True)
class DatabaseConfig:
    """SQLite database configuration."""

    path: Path


@dataclass(frozen=True, kw_only=True, slots=True)
class LlmTutorConfig:
    """Optional LLM tutor configuration."""

    provider: str
    """Tutor provider id."""
    model: str
    """Provider model id."""
    api_key: str
    """Provider API key loaded from the configured secret file."""
    timeout_seconds: float
    """Provider request timeout."""
    max_tokens: int
    """Maximum tokens to request from the tutor provider."""
    rate_limit_per_minute: int
    """Maximum tutor requests per learner per minute."""


@dataclass(frozen=True, kw_only=True, slots=True)
class UnixGroupsConfig:
    """Optional Unix group synchronization configuration."""

    grant_command: tuple[str, ...]
    """Command argv prefix that grants one user to one group."""
    revoke_command: tuple[str, ...]
    """Command argv prefix that removes one user from one group."""
    managed_groups: frozenset[str]
    """Unix groups this bot is allowed to project from SQLite."""


@dataclass(frozen=True, kw_only=True, slots=True)
class AppConfig:
    """Complete daemon configuration."""

    socket: SocketConfig
    irc: IrcConfig
    database: DatabaseConfig
    llm_tutor: LlmTutorConfig | None = None
    unix_groups: UnixGroupsConfig | None = None
    log_level: str = "INFO"


def load_config(path: Path) -> AppConfig:
    """Load daemon configuration from TOML."""
    root = _load_root(path)
    socket_table = _mapping(_required(root, "socket", "root"), "socket")
    irc_table = _mapping(_required(root, "irc", "root"), "irc")
    sasl_table = _mapping(_required(irc_table, "sasl", "irc"), "irc.sasl")
    database_table = _mapping(_required(root, "database", "root"), "database")

    return AppConfig(
        log_level=_optional_string(root, "log_level", "INFO"),
        database=DatabaseConfig(path=_path(database_table, "path", "database")),
        llm_tutor=_llm_tutor_config(root),
        unix_groups=_unix_groups_config(root),
        socket=SocketConfig(
            path=Path(_string(socket_table, "path", "socket")),
            mode=_optional_socket_mode(socket_table, "mode", 0o660),
            allowed_group=_optional_string_or_none(socket_table, "allowed_group"),
            allowed_user_ids=frozenset(_user_id_list(socket_table.get("allowed_user_ids", []))),
            backlog=_optional_positive_int(socket_table, "backlog", 100),
            max_line_bytes=_optional_positive_int(socket_table, "max_line_bytes", 16_384),
            read_timeout_seconds=_optional_positive_float(
                socket_table,
                "read_timeout_seconds",
                0.25,
            ),
            queue_size=_optional_positive_int(socket_table, "queue_size", 1_000),
        ),
        irc=IrcConfig(
            server=_string(irc_table, "server", "irc"),
            port=_optional_port(irc_table, "port", 6697),
            tls=_optional_bool(irc_table, "tls", True),
            nickname=_string(irc_table, "nickname", "irc"),
            username=_string(irc_table, "username", "irc"),
            realname=_optional_string(irc_table, "realname", "Kolam Makers Bot"),
            channels=tuple(_string_list(_required(irc_table, "channels", "irc"))),
            sasl=SaslConfig(
                mechanism=_optional_string(sasl_table, "mechanism", "PLAIN"),
                username=_string(sasl_table, "username", "irc.sasl"),
                password=_load_secret(sasl_table),
            ),
            connect_timeout_seconds=_optional_positive_float(
                irc_table,
                "connect_timeout_seconds",
                10.0,
            ),
            registration_timeout_seconds=_optional_positive_float(
                irc_table,
                "registration_timeout_seconds",
                10.0,
            ),
            read_timeout_seconds=_optional_positive_float(
                irc_table,
                "read_timeout_seconds",
                300.0,
            ),
            reconnect_initial_seconds=_optional_positive_float(
                irc_table,
                "reconnect_initial_seconds",
                1.0,
            ),
            reconnect_max_seconds=_optional_positive_float(
                irc_table,
                "reconnect_max_seconds",
                60.0,
            ),
            outbound_queue_size=_optional_positive_int(irc_table, "outbound_queue_size", 200),
            outbound_interval_seconds=_optional_positive_float(
                irc_table,
                "outbound_interval_seconds",
                1.5,
            ),
            chat_worker_count=_optional_positive_int(irc_table, "chat_worker_count", 1),
            chat_queue_size=_optional_positive_int(irc_table, "chat_queue_size", 100),
        ),
    )


def load_bot_name(path: Path) -> str:
    """Load the configured bot display name."""
    root = _load_root(path)
    return _string(_mapping(_required(root, "irc", "root"), "irc"), "nickname", "irc")


def load_database_path(path: Path) -> Path:
    """Load the configured SQLite database path without loading IRC secrets."""
    root = _load_root(path)
    return _path(_mapping(_required(root, "database", "root"), "database"), "path", "database")


def load_socket_path(path: Path) -> Path:
    """Load the configured daemon socket path without loading IRC secrets."""
    root = _load_root(path)
    return _path(_mapping(_required(root, "socket", "root"), "socket"), "path", "socket")


def load_llm_tutor_config(path: Path) -> LlmTutorConfig | None:
    """Load optional LLM tutor config without loading IRC secrets."""
    return _llm_tutor_config(_load_root(path))


def load_unix_groups_config(path: Path) -> UnixGroupsConfig | None:
    """Load optional Unix group sync config without loading IRC secrets."""
    return _unix_groups_config(_load_root(path))


def _load_root(path: Path) -> dict[str, object]:
    with path.open("rb") as file_object:
        return _mapping(cast("object", tomllib.load(file_object)), "root")


def _mapping(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ConfigError(f"{name} must be a TOML table")
    mapping = cast("dict[object, object]", value)
    if all(isinstance(key, str) for key in mapping):
        return {key: item for key, item in mapping.items() if isinstance(key, str)}
    raise ConfigError(f"{name} must be a TOML table")


def _required(table: dict[str, object], key: str, table_name: str) -> object:
    try:
        return table[key]
    except KeyError as error:
        raise ConfigError(f"{table_name}.{key} is required") from error


def _optional_mapping(
    table: dict[str, object],
    key: str,
    table_name: str,
) -> dict[str, object] | None:
    value = table.get(key)
    if value is None:
        return None
    return _mapping(value, f"{table_name}.{key}")


def _string(table: dict[str, object], key: str, table_name: str) -> str:
    value = _required(table, key, table_name)
    if isinstance(value, str) and value:
        return value
    raise ConfigError(f"{table_name}.{key} must be a non-empty string")


def _path(table: dict[str, object], key: str, table_name: str) -> Path:
    return Path(_string(table, key, table_name)).expanduser()


def _optional_string(table: dict[str, object], key: str, default: str) -> str:
    value = table.get(key, default)
    if isinstance(value, str) and value:
        return value
    raise ConfigError(f"{key} must be a non-empty string")


def _optional_string_or_none(table: dict[str, object], key: str) -> str | None:
    value = table.get(key)
    if value is None:
        return None
    if isinstance(value, str) and value:
        return value
    raise ConfigError(f"{key} must be a non-empty string when present")


def _optional_int(table: dict[str, object], key: str, default: int) -> int:
    value = table.get(key, default)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise ConfigError(f"{key} must be an integer")


def _optional_positive_int(table: dict[str, object], key: str, default: int) -> int:
    value = _optional_int(table, key, default)
    if value <= 0:
        raise ConfigError(f"{key} must be positive")
    return value


def _optional_port(table: dict[str, object], key: str, default: int) -> int:
    value = _optional_int(table, key, default)
    if not 1 <= value <= 65_535:
        raise ConfigError(f"{key} must be between 1 and 65535")
    return value


def _optional_socket_mode(table: dict[str, object], key: str, default: int) -> int:
    value = _optional_int(table, key, default)
    if not 0 <= value <= 0o777:
        raise ConfigError(f"{key} must be between 0 and 0o777")
    return value


def _optional_float(table: dict[str, object], key: str, default: float) -> float:
    value = table.get(key, default)
    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    raise ConfigError(f"{key} must be a number")


def _optional_positive_float(table: dict[str, object], key: str, default: float) -> float:
    value = _optional_float(table, key, default)
    if value <= 0:
        raise ConfigError(f"{key} must be positive")
    return value


def _optional_bool(table: dict[str, object], key: str, default: bool) -> bool:
    value = table.get(key, default)
    if isinstance(value, bool):
        return value
    raise ConfigError(f"{key} must be a boolean")


def _llm_tutor_config(root: dict[str, object]) -> LlmTutorConfig | None:
    tutor_table = _optional_mapping(root, "llm_tutor", "root")
    if tutor_table is None or not _optional_bool(tutor_table, "enabled", False):
        return None
    provider = _optional_string(tutor_table, "provider", "openrouter")
    if provider != "openrouter":
        raise ConfigError("llm_tutor.provider must be openrouter")
    rate_limit_per_minute = _optional_positive_int(
        tutor_table,
        "rate_limit_per_minute",
        DEFAULT_TUTOR_RATE_LIMIT_PER_MINUTE,
    )
    max_tokens = _optional_positive_int(
        tutor_table,
        "max_tokens",
        DEFAULT_TUTOR_MAX_TOKENS,
    )
    return LlmTutorConfig(
        provider=provider,
        model=_optional_string(tutor_table, "model", DEFAULT_TUTOR_MODEL),
        api_key=_load_named_secret(tutor_table, "api_key", "llm_tutor"),
        timeout_seconds=_optional_positive_float(
            tutor_table,
            "timeout_seconds",
            DEFAULT_TUTOR_TIMEOUT_SECONDS,
        ),
        max_tokens=max_tokens,
        rate_limit_per_minute=rate_limit_per_minute,
    )


def _unix_groups_config(root: dict[str, object]) -> UnixGroupsConfig | None:
    groups_table = _optional_mapping(root, "unix_groups", "root")
    if groups_table is None or not _optional_bool(groups_table, "enabled", False):
        return None
    return UnixGroupsConfig(
        grant_command=_command_argv(groups_table, "grant_command", "unix_groups"),
        revoke_command=_command_argv(groups_table, "revoke_command", "unix_groups"),
        managed_groups=_unix_group_set(groups_table, "managed_groups", "unix_groups"),
    )


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        items = cast("list[object]", value)
        if all(isinstance(item, str) and item for item in items):
            return [item for item in items if isinstance(item, str)]
    raise ConfigError("value must be a list of non-empty strings")


def _command_argv(table: dict[str, object], key: str, table_name: str) -> tuple[str, ...]:
    command = tuple(_string_list(_required(table, key, table_name)))
    if not command:
        raise ConfigError(f"{table_name}.{key} must not be empty")
    return command


def _unix_group_set(table: dict[str, object], key: str, table_name: str) -> frozenset[str]:
    groups = _string_list(_required(table, key, table_name))
    if not groups:
        raise ConfigError(f"{table_name}.{key} must not be empty")
    if len(set(groups)) != len(groups):
        raise ConfigError(f"{table_name}.{key} must not contain duplicates")
    for group_name in groups:
        if not is_allowed_managed_group_name(group_name):
            raise ConfigError(f"{table_name}.{key} contains unsafe Unix group: {group_name}")
    return frozenset(groups)


def _user_id_list(value: object) -> list[int]:
    if isinstance(value, list):
        items = cast("list[object]", value)
        if all(isinstance(item, int) and not isinstance(item, bool) for item in items):
            return [_non_negative_user_id(item) for item in items if isinstance(item, int)]
    raise ConfigError("allowed_user_ids must be a list of non-negative integers")


def _non_negative_user_id(user_id: int) -> int:
    if user_id < 0:
        raise ConfigError("allowed_user_ids must be a list of non-negative integers")
    return user_id


def _load_secret(table: dict[str, object]) -> str:
    password_env = table.get("password_env")
    if isinstance(password_env, str) and password_env:
        password = os.environ.get(password_env)
        if password:
            return password
        raise ConfigError(f"environment variable {password_env} is required")

    password_file = table.get("password_file")
    if isinstance(password_file, str) and password_file:
        password = Path(password_file).read_text(encoding="utf-8").strip()
        if password:
            return password
        raise ConfigError(f"password file {password_file} is empty")

    return _raise_config_error("irc.sasl.password_env or irc.sasl.password_file is required")


def _load_named_secret(table: dict[str, object], key: str, table_name: str) -> str:
    secret_file_key = f"{key}_file"
    secret_file = table.get(secret_file_key)
    if isinstance(secret_file, str) and secret_file:
        secret = Path(secret_file).read_text(encoding="utf-8").strip()
        if secret:
            return secret
        raise ConfigError(f"{table_name}.{secret_file_key} is empty")
    return _raise_config_error(f"{table_name}.{secret_file_key} is required")


def _raise_config_error(message: str) -> Never:
    raise ConfigError(message)
