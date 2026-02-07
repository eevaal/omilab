from datetime import datetime

from database.database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Table

bookmarks_table = Table(
    "bookmarks",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("lecture_id", Integer, ForeignKey("lectures.id"), primary_key=True),
    Column("created_at", DateTime, default=datetime.utcnow),
)
