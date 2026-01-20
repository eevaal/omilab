from typing import Optional
from pydantic import BaseModel, Field


# Базовая схема (общие поля)
class LectureBase(BaseModel):
    title: str
    subject: str
    # author удален отсюда, так как он не общий для "входа"
    description: str | None = None
    content: str | None = None


# Схема для СОЗДАНИЯ (внутренняя DTO для передачи в CRUD)
class LectureCreate(LectureBase):
    content: str
    author: str  # Мы добавляем его здесь, так как сервер сам его заполняет

class VoteRequest(BaseModel):
    score: int = Field(..., ge=1, le=5)


# Схема для ОТВЕТА (что видит фронтенд)
class LectureResponse(LectureBase):
    id: int
    author: str  # Фронтенду нужно знать автора
    content: str | None = None
    filename: Optional[str] = None

    class Config:
        from_attributes = True