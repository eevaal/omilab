import os
import uuid
from collections.abc import Sequence

from core.security import get_current_user
# 👇 ИМПОРТИРУЕМ НАШУ НОВУЮ ФУНКЦИЮ
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
    # Переменная, куда запишем ссылку (или имя файла)
    final_filename = None

    if file:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Можно загружать только PDF!")

        # 🔥 ГЛАВНОЕ ИЗМЕНЕНИЕ ТУТ:
        # Вместо shutil.copyfileobj мы шлём файл в R2.
        # Функция вернет прямую ссылку: https://pub-xyz.../lectures/uuid.pdf
        final_filename = await upload_file_to_r2(file, folder="lectures")

        content = content or "Загруженный PDF файл"

    else:

        os.makedirs("static/lectures", exist_ok=True)
        # Логика генерации PDF (оставляем пока локальной)
        # ⚠️ В будущем generated PDF тоже лучше лить в R2, но для беты сойдет.
        # Помни: сгенерированные файлы проживут до перезагрузки сервера!
        filename = f"{uuid.uuid4()}.pdf"

        content = content or "Текст лекции отсутствует..."
        pdf = PDFService(author=user.username, title=title)
        pdf.generate(content=content, filename=filename)

        # Для локальных файлов оставляем просто имя
        final_filename = filename

    encrypted_content = encrypt_text(content)

    lecture_data = LectureCreate(
        title=title, subject=subject, author=user.username, content=encrypted_content
    )

    # Сохраняем в БД (теперь там может быть длинная ссылка)
    return await crud.create_lecture(db=db, lecture=lecture_data, filename=final_filename)


# 👇 Этот метод теперь нужен ТОЛЬКО для старых/локальных файлов
# Файлы из R2 будут открываться напрямую по ссылке
@router.get("/download/{filename:path}")
async def download_lecture(filename: str):
    # Если это полная ссылка (значит файл в облаке) — редиректа тут нет,
    # фронтенд должен сам открывать ссылку. Но на всякий случай:
    if filename.startswith("http"):
        return {"url": filename}

    file_path = os.path.join("static", "lectures", filename)

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