"""Alembic environment configuration for no-code service."""

from __future__ import with_statement

import asyncio
import logging
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import application configuration and models
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.core.config import get_settings
from models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get application settings
settings = get_settings()

# Override the sqlalchemy.url from alembic.ini with the value from settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """Get database URL from settings."""
    return settings.database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with a database connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        # Include user-defined indexes and constraints
        include_object=include_object,
        # Render items for PostgreSQL
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def include_object(object, name, type_, reflected, compare_to):
    """Custom object inclusion logic for migrations."""
    # Include user-defined tables
    if type_ == "table" and name in [
        "users",
        "nocode_workflows",
        "nocode_components",
        "nocode_templates",
        "nocode_executions",
        "compilation_results",
        "execution_history"
    ]:
        return True

    # Include all indexes and constraints for user tables
    if type_ in ("index", "constraint") and hasattr(object, 'table') and object.table.name in [
        "users",
        "nocode_workflows",
        "nocode_components",
        "nocode_templates",
        "nocode_executions",
        "compilation_results",
        "execution_history"
    ]:
        return True

    # Exclude system tables and other auto-generated objects
    if type_ == "table" and name.startswith(("pg_", "information_schema", "alembic")):
        return False

    return True


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()