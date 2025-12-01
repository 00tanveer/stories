import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import context

# Import your Base so Alembic can autogenerate migrations
from app.db.base import Base
from dotenv import load_dotenv

load_dotenv(".env.development")


# --- Alembic Config ---
config = context.config

# Enable Alembic logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# --- Database URL from environment variable ---
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Example:\n"
        'export DATABASE_URL="postgresql+asyncpg://stories_user:PASSWORD@localhost:5432/stories_db"'
    )

# Override alembic.ini sqlalchemy.url value
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Metadata used for autogenerate
target_metadata = Base.metadata


# --- Run migrations in synchronous context ---
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,     # detect column type changes
        compare_server_default=True,  # detect server default changes
    )

    with context.begin_transaction():
        context.run_migrations()


# --- Run migrations in asynchronous context ---
def do_run_migrations(connection: Connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_async_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as async_connection:
        await async_connection.run_sync(do_run_migrations)

    await connectable.dispose()


# --- Entrypoint ---
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
