from datetime import datetime

from sqlalchemy import func

from database.database import Base
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(index=True, primary_key=True)
    username: Mapped[str] = mapped_column(index=True, unique=True)
    email: Mapped[str] = mapped_column(index=True, unique=True)
    hashed_password: Mapped[str] = mapped_column()

    is_verified: Mapped[bool] = mapped_column(index=True, default=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())