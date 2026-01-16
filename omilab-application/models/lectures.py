import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


class Lecture(Base):
    __tablename__ = 'lectures'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(index=True)
    subject: Mapped[str] = mapped_column(index=True)
    description: Mapped[str | None] = mapped_column(nullable=True)

    author: Mapped[str] = mapped_column(default="Admin")

    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())

    content: Mapped[str | None] = mapped_column()