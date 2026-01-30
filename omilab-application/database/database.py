from core.config import settings
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

DATABASE_URL = settings.database_url

engine = create_async_engine(DATABASE_URL, echo=True, pool_pre_ping=True, pool_recycle=300)

SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


async def get_db():
    async with SessionLocal() as session:
        yield session
