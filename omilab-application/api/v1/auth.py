# api/v1/auth.py
import random
from core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    decode_access_token,
)
from database.dependencies import db_dependency
from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks # <--- ИМПОРТ BackgroundTasks
from fastapi.responses import JSONResponse
from models.users import User
from schemas.users import UserCreate, UserLogin, UserResponse
from sqlalchemy import select
from pydantic import BaseModel

# Импортируем нашу функцию отправки
from utils.email import send_confirmation_code

router = APIRouter(prefix="/auth", tags=["Auth"])


# Модель для приема кода с фронтенда
class VerifyEmailRequest(BaseModel):
    email: str
    code: str


@router.post("/register")
async def register(
    user_data: UserCreate,
    db: db_dependency,
    background_tasks: BackgroundTasks # <--- Добавляем в аргументы
):
    # Проверки на существование
    q_username = select(User).where(User.username == user_data.username)
    if (await db.execute(q_username)).scalars().first():
        raise HTTPException(status_code=400, detail="Пользователь с данным именем уже существует")

    q_email = select(User).where(User.email == user_data.email)
    if (await db.execute(q_email)).scalars().first():
        raise HTTPException(status_code=400, detail="Пользователь с данным email уже существует")

    hashed_pwd = get_password_hash(user_data.password)

    # Генерируем код (6 цифр)
    activation_code = str(random.randint(100000, 999999))

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_pwd,
        email_confirmed=False,
        confirmation_code=activation_code
    )

    db.add(new_user)
    await db.commit()
    # await db.refresh(new_user) # Убираем лишний запрос для скорости

    # --- ГЛАВНОЕ ИЗМЕНЕНИЕ: Отправка в фоне ---
    # Мы просто добавляем задачу в очередь, сервер выполнит её после ответа юзеру
    background_tasks.add_task(send_confirmation_code, user_data.email, activation_code)
    # ------------------------------------------

    return {"message": "User created", "email": user_data.email}


# Остальной код без изменений
@router.post("/verify-email")
async def verify_email_code(data: VerifyEmailRequest, db: db_dependency):
    query = select(User).where(User.email == data.email)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if user.email_confirmed:
        return {"message": "Почта уже подтверждена"}

    if user.confirmation_code == data.code:
        user.email_confirmed = True
        user.confirmation_code = None
        await db.commit()
        return {"message": "Успех"}
    else:
        raise HTTPException(status_code=400, detail="Неверный код")


@router.post("/login")
async def login(user_data: UserLogin, db: db_dependency):
    query = select(User).where(User.username == user_data.username)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверные данные")

    if not user.email_confirmed:
        raise HTTPException(
            status_code=403,
            detail="Почта не подтверждена. Введите код, отправленный на email."
        )

    access_token = create_access_token(data={"sub": user.username})
    response = JSONResponse(content={"status": "ok", "username": user.username})
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True, path="/")
    return response


@router.post("/logout")
async def logout():
    response = JSONResponse(content={"message": "Вы успешно вышли"})
    response.delete_cookie(key="access_token", path="/", httponly=True)
    return response


async def get_current_user(request: Request, db: db_dependency):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Не авторизован")
    try:
        scheme, _, param = token.partition(" ")
        token_str = param if param else scheme
        payload = decode_access_token(token_str)
        username: str = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Ошибка авторизации")

    query = select(User).where(User.username == username)
    result = await db.execute(query)
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user