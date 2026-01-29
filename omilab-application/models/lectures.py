from datetime import datetime

from database.database import Base
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Lecture(Base):
    __tablename__ = "lectures"

    rating = relationship("LectureRating", backref="lectures")

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(index=True)
    subject: Mapped[str] = mapped_column(index=True)
    description: Mapped[str | None] = mapped_column(nullable=True)

    author: Mapped[str] = mapped_column(default="Admin")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    content: Mapped[str | None] = mapped_column()

    filename: Mapped[str] = mapped_column(nullable=True)


class LectureRating(Base):
    __tablename__ = "lecture_ratings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    lecture_id: Mapped[int] = mapped_column(ForeignKey("lectures.id"))
    score: Mapped[int] = mapped_column(default=5)
