from typing import Sequence, Optional
from fastapi import APIRouter, Form, File, UploadFile, HTTPException, Depends # <-- Добавил Depends
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import models.lectures
from models.lectures import LectureRating
from database import crud
from database.dependencies import db_dependency
from schemas.lectures import LectureCreate, LectureResponse, VoteRequest
import os
import shutil
import uuid

from cryptography.fernet import Fernet

from services.pdf_generator import PDFService

from core.security import get_current_user
from models.users import User
from models.lectures import LectureRating

router = APIRouter(prefix="/api/v1/lectures")

@router.get("/search", response_model=Sequence[LectureResponse])
async def search_lectures(q: str, db: db_dependency):
    return await crud.search_lectures(db, query=q)


@router.post("/", response_model=LectureResponse)
async def create_lecture(
        title: str = Form(...),
        subject: str = Form(...),
        content: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None),
        user: User = Depends(get_current_user),
        db: db_dependency = None
):
    filename = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join("static", "lectures", filename)

    if file:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Можно загружать только PDF!")

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        content = content or "Загруженный PDF файл"
    else:
        content = content or "Текст лекции отсутствует..."
        pdf = PDFService(author=user.username, title=title)
        pdf.generate(content=content, filename=filename)

    encrypted_content = encrypt_text(content) # ENCRYPT LECTURE

    lecture_data = LectureCreate(
        title=title,
        subject=subject,
        author=user.username,
        content=encrypted_content
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

# --- ENCRYPT LECTURES ---

cipher_suite = Fernet(os.getenv("SECRET_KEY_LECTURES"))

def encrypt_text(text: str) -> str:
    if not text: return ""
    return cipher_suite.encrypt(text.encode()).decode()

def decrypt_text(text: str) -> str:
    if not text: return ""
    try:
        return cipher_suite.decrypt(text.encode()).decode()
    except:
        return text



# --- RATING ---

@router.post("/{id}/rate")
async def rate_lecture(
        id: int,
        vote: VoteRequest,
        db: db_dependency,
        user: dict = Depends(get_current_user)
):
    if not user:
        raise HTTPException(status_code=401, detail="Войдите, чтобы оценить")

    # Проверяем, голосовал ли уже этот юзер
    query = select(LectureRating).where(
        LectureRating.user_id == user.id,
        LectureRating.lecture_id == id
    )
    result = await db.execute(query)  # <--- Тут await у тебя был, это хорошо

    existing_vote = result.scalar_one_or_none()

    if existing_vote:
        existing_vote.score = vote.score
    else:
        new_vote = LectureRating(
            user_id=user.id,
            lecture_id=id,
            score=vote.score
        )
        db.add(new_vote)

    # 🔥 ГЛАВНОЕ ИСПРАВЛЕНИЕ: Добавили await
    await db.commit()

    return {"message": "Оценка сохранена", "score": vote.score}