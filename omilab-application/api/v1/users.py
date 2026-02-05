import asyncio
import uuid

from core.security import get_current_user, get_password_hash
from database.database import get_db
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from models.users import User, subscriptions
from schemas.users import UserUpdate
from services.storage import storage_service
from sqlalchemy import update, select, func, insert, delete, and_
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


@router.post("/{username}/toggle-follow")
async def toggle_follow(
        username: str,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    # 1. Ищем ID пользователя, на которого хотим подписаться
    # Нам не нужен весь объект с лекциями, только ID
    query = select(User.id).where(User.username == username)
    result = await db.execute(query)
    target_user_id = result.scalar_one_or_none()

    if not target_user_id:
        raise HTTPException(404, detail="Пользователь не найден")

    if target_user_id == current_user.id:
        raise HTTPException(400, detail="Нельзя подписаться на самого себя")

    # 2. Проверяем наличие связи напрямую в таблице subscriptions
    # Это "легкий" запрос, который не вызывает MissingGreenlet
    stmt_check = select(subscriptions).where(
        and_(
            subscriptions.c.follower_id == current_user.id,
            subscriptions.c.followed_id == target_user_id
        )
    )
    result_check = await db.execute(stmt_check)
    is_following = result_check.first() is not None

    action = ""

    if is_following:
        # ОТПИСЫВАЕМСЯ (Удаляем запись из таблицы)
        stmt = delete(subscriptions).where(
            and_(
                subscriptions.c.follower_id == current_user.id,
                subscriptions.c.followed_id == target_user_id
            )
        )
        action = "unfollowed"
    else:
        # ПОДПИСЫВАЕМСЯ (Вставляем запись)
        stmt = insert(subscriptions).values(
            follower_id=current_user.id,
            followed_id=target_user_id
        )
        action = "followed"

    await db.execute(stmt)
    await db.commit()

    # 3. Считаем и возвращаем новое количество подписчиков
    count_query = select(func.count()).select_from(subscriptions).where(
        subscriptions.c.followed_id == target_user_id
    )
    new_followers_count = await db.scalar(count_query)

    return {
        "status": "ok",
        "action": action,
        "new_followers_count": new_followers_count
    }



