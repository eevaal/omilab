from models.lectures import Lecture
from schemas.lectures import LectureCreate
from sqlalchemy import Sequence, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_lecture(db: AsyncSession, lecture: LectureCreate, filename: str = None):
    db_lecture = Lecture(
        title=lecture.title,
        content=lecture.content,
        author=lecture.author,
        subject=lecture.subject,
        filename=filename,
    )
    db.add(db_lecture)
    await db.commit()
    await db.refresh(db_lecture)
    return db_lecture


"""
async def get_all_lectures(db: AsyncSession, skip: int = 0, limit: int = 100) -> Sequence[Lecture]:
    query = select(Lecture).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
"""


async def get_recent_lectures(db: AsyncSession, limit: int = 3):
    query = select(Lecture).order_by(Lecture.id.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def search_lectures(db: AsyncSession, query: str) -> Sequence[Lecture]:
    search_term = f"%{query}%"

    stmt = select(Lecture).where(
        or_(Lecture.title.ilike(search_term), Lecture.subject.ilike(search_term))
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_lecture_by_id(db: AsyncSession, lecture_id: int):
    query = select(Lecture).where(Lecture.id == lecture_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()
