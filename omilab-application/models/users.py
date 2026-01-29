from datetime import datetime

from database.database import Base
from sqlalchemy import Column, ForeignKey, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

subscriptions = Table(
    "subscriptions",
    Base.metadata,
    Column("follower_id", ForeignKey("users.id"), primary_key=True),
    Column("following_id", ForeignKey("users.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(index=True, primary_key=True)
    username: Mapped[str] = mapped_column(index=True, unique=True)
    email: Mapped[str] = mapped_column(index=True, unique=True)
    hashed_password: Mapped[str] = mapped_column()

    is_verified: Mapped[bool] = mapped_column(index=True, default=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    avatar_url: Mapped[str] = mapped_column(nullable=True)

    following: Mapped[list["User"]] = relationship(
        secondary=subscriptions,
        primaryjoin=(id == subscriptions.c.follower_id),
        secondaryjoin=(id == subscriptions.c.followed_id),
        back_populates="followers",
    )

    followers: Mapped[list["User"]] = relationship(
        secondary=subscriptions,
        primaryjoin=(id == subscriptions.c.followed_id),
        secondaryjoin=(id == subscriptions.c.follower_id),
        back_populates="following",
    )
