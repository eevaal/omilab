from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# 1. Вычисляем абсолютный путь к папке проекта
# __file__ - это путь к текущему файлу (database.py)
# .parent - папка 'database'
# .parent.parent - папка 'omilab-application'
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Указываем явный путь к файлу БД
# Теперь база всегда будет лежать внутри 'omilab-application', откуда бы вы ни запускали проект
DB_PATH = BASE_DIR / "omilab.db"

DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# Создаем движок
engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session


