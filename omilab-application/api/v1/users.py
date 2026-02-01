import uuid
import asyncio

from core.security import get_current_user
from database.database import get_db
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from models.users import User
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from services.storage import storage_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/me/avatar")
async def upload_avatar(  # <--- ВЕРНУЛИ ASYNC
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Проверка типа файла
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, detail="Файл должен быть изображением")

    # 2. Генерируем имя файла
    file_ext = file.filename.split(".")[-1]
    new_filename = f"avatars/{uuid.uuid4()}.{file_ext}"

    # 3. ЗАГРУЗКА В R2 (В ФОНОВОМ ПОТОКЕ)
    try:
        # asyncio.to_thread запускает синхронную функцию в отдельном потоке,
        # чтобы основной сервер не завис, пока файл летит в облако.
        avatar_url = await asyncio.to_thread(
            storage_service.upload_file,
            file_obj=file.file,
            object_name=new_filename,
            content_type=file.content_type
        )
    except Exception as e:
        print(f"Upload error: {e}") # Полезно видеть ошибку в логах
        raise HTTPException(500, detail="Не удалось загрузить изображение в облако")

    # 4. Обновление базы данных (Теперь работает, потому что есть await)
    stmt = update(User).where(User.id == user.id).values(avatar_url=avatar_url)
    await db.execute(stmt)  # <--- ТЕПЕРЬ БАЗА СЛУШАЕТСЯ
    await db.commit()       # <--- И СОХРАНЯЕТ

    return {"status": "ok", "avatar_url": avatar_url}
