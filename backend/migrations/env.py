from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.config import get_settings  # noqa: E402
from app.db import Base  # noqa: E402

# Registers every model on Base.metadata. Without this import, --autogenerate
# compares against empty metadata and cheerfully produces empty migrations.
import app.models  # noqa: F401,E402

target_metadata = Base.metadata

# The URL is read straight from Settings and handed to create_engine, never
# written into the ini via config.set_main_option. alembic.ini is parsed by
# ConfigParser, which treats "%" as interpolation syntax — so a percent-encoded
# character in the password (e.g. "%23" for "#") raises
# "invalid interpolation syntax" before a connection is ever attempted.
DATABASE_URL = get_settings().migration_database_url


def run_migrations_offline() -> None:
    """Emit migrations as SQL, without connecting."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live connection."""
    if not DATABASE_URL:
        raise RuntimeError(
            "No migration database URL. Set DIRECT_DATABASE_URL (or "
            "DATABASE_URL) in the repo-root .env."
        )

    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
