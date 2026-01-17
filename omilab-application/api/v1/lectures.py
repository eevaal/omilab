from typing import Sequence, Optional
from fastapi import APIRouter, Form, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from database import crud
from database.dependencies import db_dependency
from schemas.lectures import LectureCreate, LectureResponse
import os

import shutil # Для сохранения файла

from services.pdf_generator import PDFService
import uuid

router = APIRouter(prefix="/api/v1/lectures")

@router.get("/search", response_model=Sequence[LectureResponse])
async def search_lectures(q: str, db: db_dependency):
    return await crud.search_lectures(db, query=q)


@router.post("/", response_model=LectureResponse)
async def create_lecture(
        # Принимаем данные как Form (для поддержки файлов), а не JSON
        title: str = Form(...),
        subject: str = Form(...),
        author: str = Form(...),
        content: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None),  # Поле для файла
        db: db_dependency = None  # Твой db_dependency (возможно, он у тебя без default, проверь)
):
    # 1. Генерируем имя
    filename = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join("static", "lectures", filename)

    # 2. Логика: Если загрузили файл -> сохраняем. Если нет -> генерируем.
    if file:
        # Проверка расширения
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Можно загружать только PDF!")

        # Сохраняем байты файла на диск
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        content = content or "Загруженный PDF файл"
    else:
        # Генерируем PDF, как раньше
        content = content or "Текст лекции отсутствует..."
        pdf = PDFService(author=author, title=title)
        pdf.generate(content=content, filename=filename)

    # 3. Собираем объект для БД вручную (т.к. мы не использовали LectureCreate на входе)
    lecture_data = LectureCreate(
        title=title,
        subject=subject,
        author=author,
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