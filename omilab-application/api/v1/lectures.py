from typing import Sequence, Optional
from fastapi import APIRouter, Form, File, UploadFile, HTTPException, Depends # <-- Добавил Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database import crud
from database.dependencies import db_dependency
from schemas.lectures import LectureCreate, LectureResponse
import os
import shutil
import uuid

from services.pdf_generator import PDFService

# 👇 ИМПОРТЫ ДЛЯ ПОЛУЧЕНИЯ ЮЗЕРА
from core.security import get_current_user
from models.users import User

router = APIRouter(prefix="/api/v1/lectures")

@router.get("/search", response_model=Sequence[LectureResponse])
async def search_lectures(q: str, db: db_dependency):
    return await crud.search_lectures(db, query=q)


@router.post("/", response_model=LectureResponse)
async def create_lecture(
        title: str = Form(...),
        subject: str = Form(...),
        # author: str = Form(...),  <-- УДАЛЕНО! Теперь мы не верим форме
        content: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None),
        user: User = Depends(get_current_user), # <-- БЕРЕМ ЮЗЕРА ИЗ ТОКЕНА
        db: db_dependency = None
):
    # 1. Генерируем имя
    filename = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join("static", "lectures", filename)

    # 2. Логика файла
    if file:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Можно загружать только PDF!")

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        content = content or "Загруженный PDF файл"
    else:
        content = content or "Текст лекции отсутствует..."
        # Используем user.username вместо переданного author
        pdf = PDFService(author=user.username, title=title)
        pdf.generate(content=content, filename=filename)

    # 3. Собираем объект
    lecture_data = LectureCreate(
        title=title,
        subject=subject,
        author=user.username, # <-- ПОДСТАВЛЯЕМ РЕАЛЬНОГО АВТОРА
        content=content
    )

    return await crud.create_lecture(db=db, lecture=lecture_data, filename=filename)


@router.get("/download/{filename}")
async def download_lecture(filename: str):
    file_path = os.path.join("static", "lectures", filename)

    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/pdf'
        )
    return {"error": "File not found"}