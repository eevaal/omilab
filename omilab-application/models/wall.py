from datetime import datetime
from sqlalchemy import Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database.database import Base

class WallPost(Base):
    __tablename__ = "wall_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    author = relationship("User", foreign_keys=[author_id], backref="authored_posts")

    target_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    target_user = relationship("User", foreign_keys=[target_user_id], backref="wall_posts")