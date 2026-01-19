from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from core.security import get_password_hash, verify_password
from database.dependencies import db_dependency
from models.users import User
from schemas.users import UserResponse, UserCreate, UserLogin

from core.security import create_access_token, verify_password
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post('/register', response_model=UserResponse)
async def register(user_data: UserCreate, db: db_dependency):
    q_username = select(User).where(User.username == user_data.username)
    result_username = await db.execute(q_username)
    existing_user = result_username.scalars().first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Это имя пользователя занято")

    q_email = select(User).where(User.email == user_data.email)
    result_email = await db.execute(q_email)
    existing_email = result_email.scalars().first()

    if existing_email:
        raise HTTPException(status_code=400, detail="Это имя пользователя занято")

    hashed_pwd = get_password_hash(user_data.password)

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_pwd
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/login")
async def login(user_data: UserLogin, db: db_dependency):
    # 1. Поиск юзера (как у тебя было)
    query = select(User).where(User.username == user_data.username)  # Добавь email если надо
    result = await db.execute(query)
    user = result.scalars().first()

    # 2. Проверка пароля
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверные данные")

    # 3. СОЗДАНИЕ ТОКЕНА (Новая часть)
    access_token = create_access_token(data={"sub": user.username})

    # 4. Формируем ответ и КЛАДЕМ В КУКИ
    response = JSONResponse(content={"status": "ok", "username": user.username})

    # key="access_token" - название куки
    # value - сам токен
    # httponly=True - защита от кражи через JS
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        path="/"  # <--- ВОТ ЭТО ВАЖНО ДОБАВИТЬ
    )

    return response


@router.post("/logout")
async def logout():
    # Создаем объект ответа вручную
    response = JSONResponse(content={"message": "Вы успешно вышли"})

    # Удаляем куку (Важно: path="/" обязателен, иначе удалится не та кука)
    response.delete_cookie(key="access_token", path="/", httponly=True)

    return response