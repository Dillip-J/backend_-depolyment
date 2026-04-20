import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# 1. Import dotenv
from dotenv import load_dotenv

# 🚨 THE FIX: Load the .env file BEFORE you import the database!
load_dotenv()

# 2. Add your project directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# NOW it is safe to import the database because the environment is loaded!
from database import Base
from models import users, providers, bookings, catalog 

# this is the Alembic Config object
config = context.config

# Override the alembic.ini url with your secure .env URL!
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 4. Set the target metadata
target_metadata = Base.metadata

# ... KEEP THE REST OF YOUR FUNCTIONS (run_migrations_offline, etc) BELOW THIS EXACTLY AS THEY ARE ...
# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()