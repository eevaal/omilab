from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pathlib import Path
import shutil
import uuid

from database.database import get_db
from models.users import User
from core.security import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/me/avatar")
async def upload_avatar(
        file: UploadFile = File(...),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, detail="Файл должен быть изображением")

    file_ext = file.filename.split(".")[-1]
    new_filename = f"{uuid.uuid4()}.{file_ext}"
    save_path = Path("static/images/avatars") / new_filename

    # Создаем папку если нет
    save_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        print(f"Error saving file: {e}")  # Полезно для отладки
        raise HTTPException(500, detail="Ошибка при сохранении файла")

    web_path = f"/static/images/avatars/{new_filename}"

    # 👇 ВОТ ТУТ ИЗМЕНЕНИЯ: Явное обновление через update
    # Это гарантирует, что база данных увидит новую ссылку
    stmt = (
        update(User)
        .where(User.id == user.id)
        .values(avatar_url=web_path)
    )
    await db.execute(stmt)
    await db.commit()

    return {"status": "ok", "avatar_url": web_path}

