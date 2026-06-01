from datetime import datetime

from pydantic import BaseModel, Field


class WallPostCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    target_user_id: int


class WallPostDisplay(BaseModel):
    id: int
    content: str
    created_at: datetime
    author_username: str

    author_avatar_url: str | None = None
    author_is_verified: bool = False

    class Config:
        from_attributes = True
