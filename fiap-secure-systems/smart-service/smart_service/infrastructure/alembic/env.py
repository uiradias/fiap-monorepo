"""Alembic env. Reads the database URL from `SMART_DATABASE_URL`."""
from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# Resolve URL from env so the same Alembic config works in containers and Testcontainers.
db_url = os.environ.get("SMART_DATABASE_URL")
if not db_url:
    raise RuntimeError("SMART_DATABASE_URL is not set")
config.set_main_option("sqlalchemy.url", db_url)

# We don't import models for autogenerate — the initial schema is hand-written.
target_metadata = None


def run_migrations_offline() -> None:
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
