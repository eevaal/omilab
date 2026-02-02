import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ------------------------------------------------------------------------
# 1. НАСТРОЙКА ПУТЕЙ (Чтобы Alembic видел твои папки)
# ------------------------------------------------------------------------
current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.dirname(current_path)

# Если папка с кодом называется omilab-application, добавляем её в путь
app_path = os.path.join(root_path, "omilab-application")
sys.path.insert(0, app_path)
sys.path.insert(0, root_path)  # На всякий случай добавляем и корень

# ------------------------------------------------------------------------
# 2. ЧТЕНИЕ КОНФИГА И ПЕРЕМЕННЫХ ОКРУЖЕНИЯ
# ------------------------------------------------------------------------
config = context.config

# Перехватываем DATABASE_URL из терминала/системы
# Это исправит ошибку "Context impl SQLiteImpl"
db_url = os.environ.get("DATABASE_URL")
if db_url:
    # Важно: Для этого скрипта (async) ссылка должна быть с +asyncpg
    config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ------------------------------------------------------------------------
# 3. ИМПОРТ МОДЕЛЕЙ (Самая важная часть для autogenerate)
# ------------------------------------------------------------------------
# Сначала импортируем Base
from database.database import Base

# Потом ВСЕ модели, которые должны попасть в миграцию
from models.users import User
from models.lectures import Lecture
from models.bookmarks import bookmarks_table

# Привязываем метаданные
target_metadata = Base.metadata

# ------------------------------------------------------------------------
# 4. ЛОГИКА МИГРАЦИЙ (OFFLINE / ONLINE)
# ------------------------------------------------------------------------


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


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using Async engine."""

    # Создаем асинхронный движок на основе URL из конфига
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
