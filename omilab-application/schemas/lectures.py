from typing import Optional

from pydantic import BaseModel

# Базовая схема
class LectureBase(BaseModel):
    title: str
    subject: str
    author: str          # <--- Мы добавили автора, его не хватало!
    description: str | None = None  # Сделали необязательным (фронт его не шлет)
    content: str | None = None


# Схема для ВХОДЯЩИХ данных (создание)
class LectureCreate(LectureBase):
    content: str         # Обязательно ждем HTML

# Схема для ИСХОДЯЩИХ данных (ответ сервера)
class LectureResponse(LectureBase):
    id: int
    content: str | None = None
    filename: Optional[str] = None

    class Config:
        from_attributes = True