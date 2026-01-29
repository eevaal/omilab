from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

BASE_DIR = Path(__file__).resolve().parent.parent


DB_PATH = BASE_DIR / "omilab.db"

DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"


engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


async def get_db():
    async with SessionLocal() as session:
        yield session
