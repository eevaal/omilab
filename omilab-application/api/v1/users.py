import asyncio
import uuid

from core.security import get_current_user
from database.database import get_db
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from models.users import User
from services.storage import storage_service
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, detail="Файл должен быть изображением")

    file_ext = file.filename.split(".")[-1]
    new_filename = f"avatars/{uuid.uuid4()}.{file_ext}"

    try:
        avatar_url = await asyncio.to_thread(
            storage_service.upload_file,
            file_obj=file.file,
            object_name=new_filename,
            content_type=file.content_type,
        )
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(500, detail="Не удалось загрузить изображение в облако") from e

    stmt = update(User).where(User.id == user.id).values(avatar_url=avatar_url)
    await db.execute(stmt)
    await db.commit()

    return {"status": "ok", "avatar_url": avatar_url}
