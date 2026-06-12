import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

DATABASE_URL = (
    "mysql+pymysql://"
    f"{os.getenv('DB_USER', 'okasdev')}:{os.getenv('DB_PASSWORD', '')}"
    f"@{os.getenv('DB_HOST', '127.0.0.1')}:{os.getenv('DB_PORT', '3306')}"
    f"/{os.getenv('DB_NAME', 'okas_signature')}"
    "?charset=utf8mb4"
)
config.set_main_option("sqlalchemy.url", DATABASE_URL)

from app.models.base import Base
import app.models.auth
import app.models.projects
import app.models.location
import app.models.controllers
import app.models.devices
import app.models.scenes
import app.models.state
import app.models.voice
import app.models.docs_inventory
import app.models.firmware
import app.models.support
import app.models.drivers
import app.models.access
import app.models.audit

target_metadata = Base.metadata


def run_migrations_offline() -> None:
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
