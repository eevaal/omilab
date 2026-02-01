import uuid

from core.security import get_current_user
from database.database import get_db
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from models.users import User
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from services.storage import storage_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/me/avatar")
def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Проверка типа файла (как и было)
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, detail="Файл должен быть изображением")

    # 2. Генерируем имя файла
    file_ext = file.filename.split(".")[-1]
    new_filename = f"avatars/{uuid.uuid4()}.{file_ext}" # Добавил папку avatars/ для порядка в бакете

    # 3. ЗАГРУЗКА В R2 (Магия здесь)
    try:
        # file.file - это файловый объект, который хочет boto3
        avatar_url = storage_service.upload_file(
            file_obj=file.file,
            object_name=new_filename,
            content_type=file.content_type
        )
    except Exception as e:
        # Логируем ошибку для себя, пользователю отдаем 500
        raise HTTPException(500, detail="Не удалось загрузить изображение в облако")

    # 4. Обновление базы данных (Теперь сохраняем полную ссылку на R2)
    stmt = update(User).where(User.id == user.id).values(avatar_url=avatar_url)
    db.execute(stmt)
    db.commit()

    return {"status": "ok", "avatar_url": avatar_url}
