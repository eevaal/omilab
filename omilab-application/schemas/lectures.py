from pydantic import BaseModel, Field


class LectureBase(BaseModel):
    title: str
    subject: str

    description: str | None = None
    content: str | None = None


class LectureCreate(LectureBase):
    content: str
    author: str


class VoteRequest(BaseModel):
    score: int = Field(..., ge=1, le=5)


class LectureResponse(LectureBase):
    id: int
    author: str
    content: str | None = None
    filename: str | None = None

    class Config:
        from_attributes = True
