from pydantic import BaseModel
from datetime import datetime

class WallPostCreate(BaseModel):
    content: str
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