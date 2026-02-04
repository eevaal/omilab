import asyncio
import uuid

from core.security import get_current_user, get_password_hash
from database.database import get_db
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from models.users import User
from schemas.users import UserUpdate
from services.storage import storage_service
from sqlalchemy import update, select
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

@router.patch("/me")  
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    if user_update.email and user_update.email != current_user.email:
        existing_user = await db.execute(select(User).where(User.email == user_update.email))
        if existing_user.scalar():
            raise HTTPException(status_code=400, detail="Этот Email уже занят")
        current_user.email = user_update.email

    
    if user_update.password:
        
        current_user.hashed_password = get_password_hash(user_update.password)

    
    try:
        await db.commit()
        await db.refresh(current_user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при сохранении")

    return {"status": "ok", "message": "Профиль обновлен"}



