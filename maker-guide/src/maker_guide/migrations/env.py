"""Alembic environment for SQLite migrations."""

from __future__ import annotations

import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context as alembic_context
from sqlalchemy import create_engine
from sqlalchemy import pool as sqlalchemy_pool

from maker_guide.repositories.helpers import ensure_database_file_permissions

_DATABASE_PATH_ENVIRONMENT_VARIABLE = "MAKER_GUIDE_DB_PATH"


def _database_url() -> str:
    database_path = os.environ.get(_DATABASE_PATH_ENVIRONMENT_VARIABLE)
    if database_path:
        return f"sqlite:///{Path(database_path)}"
    configured_url = alembic_context.config.get_main_option("sqlalchemy.url")
    if configured_url is None:
        raise RuntimeError("alembic sqlalchemy.url is not configured")
    return configured_url


def run_migrations_offline() -> None:
    """Generate SQL without opening a database connection."""
    alembic_context.configure(
        url=_database_url(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with alembic_context.begin_transaction():
        alembic_context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against the configured SQLite database."""
    engine = create_engine(_database_url(), poolclass=sqlalchemy_pool.NullPool)
    with engine.connect() as connection:
        alembic_context.configure(connection=connection)
        with alembic_context.begin_transaction():
            alembic_context.run_migrations()
    if database_path := _sqlite_database_path():
        ensure_database_file_permissions(database_path)


def _sqlite_database_path() -> Path | None:
    database_path = os.environ.get(_DATABASE_PATH_ENVIRONMENT_VARIABLE)
    if database_path:
        return Path(database_path)
    database_url = _database_url()
    if database_url == "sqlite:///:memory:" or not database_url.startswith("sqlite:///"):
        return None
    return Path(database_url.removeprefix("sqlite:///"))


if alembic_context.config.config_file_name is not None:
    fileConfig(alembic_context.config.config_file_name)

if alembic_context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
