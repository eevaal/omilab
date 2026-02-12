from datetime import datetime

from database.database import Base
from models.bookmarks import bookmarks_table
from sqlalchemy import Column, ForeignKey, Table, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

subscriptions = Table(
    "subscriptions",
    Base.metadata,
    Column("follower_id", ForeignKey("users.id"), primary_key=True),
    Column("followed_id", ForeignKey("users.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(index=True, primary_key=True)
    username: Mapped[str] = mapped_column(index=True, unique=True)
    email: Mapped[str] = mapped_column(index=True, unique=True)
    hashed_password: Mapped[str] = mapped_column()

    is_verified: Mapped[bool] = mapped_column(index=True, default=False)
    plus_until: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    @property
    def is_plus(self) -> bool:
        if not self.plus_until:
            return False
        return self.plus_until > datetime.utcnow()

    email_confirmed: Mapped[bool] = mapped_column(default=False, nullable=True)
    confirmation_code: Mapped[str] = mapped_column(nullable=True)

    is_banned: Mapped[bool] = mapped_column(default=False, nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    avatar_url: Mapped[str] = mapped_column(nullable=True)

    following: Mapped[list["User"]] = relationship(
        secondary=subscriptions,
        primaryjoin=(id == subscriptions.c.follower_id),
        secondaryjoin=(id == subscriptions.c.followed_id),
        back_populates="followers",
        lazy="selectin",
    )

    followers: Mapped[list["User"]] = relationship(
        secondary=subscriptions,
        primaryjoin=(id == subscriptions.c.followed_id),
        secondaryjoin=(id == subscriptions.c.follower_id),
        back_populates="following",
        lazy="selectin",
    )

    bookmarks = relationship(
        "Lecture", secondary=bookmarks_table, backref="bookmarked_by", lazy="selectin"
    )
