import os
import uuid
from collections.abc import Sequence

from core.security import get_current_user
from core.storage import upload_file_to_r2
from cryptography.fernet import Fernet
from database import crud
from database.dependencies import db_dependency
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from models.lectures import LectureRating
from models.users import User
from schemas.lectures import LectureCreate, LectureResponse, VoteRequest
from services.pdf_generator import PDFService
from sqlalchemy import select
from utils.sanitize import sanitize_html
from utils.uploads import validate_pdf_upload

router = APIRouter(prefix="/api/v1/lectures")


@router.get("/search", response_model=Sequence[LectureResponse])
async def search_lectures(q: str, db: db_dependency):
    return await crud.search_lectures(db, query=q)


@router.post("/", response_model=LectureResponse)
async def create_lecture(
    title: str = Form(...),
    subject: str = Form(...),
    content: str | None = Form(None),
    file: UploadFile | None = File(None),
    user: User = Depends(get_current_user),
    db: db_dependency = None,
):
    final_filename = None

    if file:
        await validate_pdf_upload(file)
        file.filename = "lecture.pdf"

        final_filename = await upload_file_to_r2(file, folder="lectures")

        content = content or "Загруженный PDF файл"

    else:
        os.makedirs("static/lectures", exist_ok=True)

        filename = f"{uuid.uuid4()}.pdf"

        content = sanitize_html(content or "Текст лекции отсутствует...")
        pdf = PDFService(author=user.username, title=title)
        pdf.generate(content=content, filename=filename)

        final_filename = filename

    encrypted_content = encrypt_text(sanitize_html(content))

    lecture_data = LectureCreate(
        title=title, subject=subject, author=user.username, content=encrypted_content
    )

    return await crud.create_lecture(db=db, lecture=lecture_data, filename=final_filename)


@router.get("/download/{filename:path}")
async def download_lecture(filename: str):
    if filename.startswith("http"):
        return {"url": filename}

    base_path = os.path.abspath(os.path.join("static", "lectures"))
    file_path = os.path.abspath(os.path.join(base_path, filename))

    if not file_path.startswith(base_path + os.sep):
        raise HTTPException(status_code=400, detail="Invalid filename")

    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename=filename, media_type="application/pdf")
    return {"error": "File not found"}


cipher_suite = Fernet(os.getenv("SECRET_KEY_LECTURES"))


def encrypt_text(text: str) -> str:
    if not text:
        return ""
    return cipher_suite.encrypt(text.encode()).decode()


def decrypt_text(text: str) -> str:
    if not text:
        return ""
    try:
        return cipher_suite.decrypt(text.encode()).decode()
    except Exception:
        return text


@router.post("/{id}/rate")
async def rate_lecture(
    id: int,
    vote: VoteRequest,
    db: db_dependency,
    user: dict = Depends(get_current_user),
):
    if not user:
        raise HTTPException(status_code=401, detail="Войдите, чтобы оценить")

    query = select(LectureRating).where(
        LectureRating.user_id == user.id, LectureRating.lecture_id == id
    )
    result = await db.execute(query)

    existing_vote = result.scalar_one_or_none()

    if existing_vote:
        existing_vote.score = vote.score
    else:
        new_vote = LectureRating(user_id=user.id, lecture_id=id, score=vote.score)
        db.add(new_vote)

    await db.commit()

    return {"message": "Оценка сохранена", "score": vote.score}
