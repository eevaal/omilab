import hmac
import os
import secrets
from datetime import datetime, timedelta

from core.config import settings
from core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    hash_confirmation_code,
    verify_password,
)
from database.dependencies import db_dependency
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from models.users import User
from pydantic import BaseModel
from schemas.users import UserCreate, UserLogin
from sqlalchemy import select
from utils.email import send_confirmation_code

router = APIRouter(prefix="/auth", tags=["Auth"])
COOKIE_SECURE = (
    os.getenv("COOKIE_SECURE", "true" if os.getenv("RENDER") else "false").lower() == "true"
)
CONFIRMATION_CODE_TTL_MINUTES = 10
CONFIRMATION_CODE_MAX_ATTEMPTS = 5


class VerifyEmailRequest(BaseModel):
    email: str
    code: str


def _make_confirmation_record(code: str) -> str:
    expires_at = int(
        (datetime.utcnow() + timedelta(minutes=CONFIRMATION_CODE_TTL_MINUTES)).timestamp()
    )
    return f"{hash_confirmation_code(code)}:{expires_at}:0"


def _parse_confirmation_record(record: str | None) -> tuple[str, int, int] | None:
    if not record:
        return None

    try:
        code_hash, expires_at, attempts = record.split(":", 2)
        return code_hash, int(expires_at), int(attempts)
    except ValueError:
        return None


@router.post("/register")
async def register(user_data: UserCreate, db: db_dependency, background_tasks: BackgroundTasks):
    q_username = select(User).where(User.username == user_data.username)
    if (await db.execute(q_username)).scalars().first():
        raise HTTPException(status_code=400, detail="Пользователь с данным именем уже существует")

    q_email = select(User).where(User.email == user_data.email)
    if (await db.execute(q_email)).scalars().first():
        raise HTTPException(status_code=400, detail="Пользователь с данным email уже существует")

    hashed_pwd = get_password_hash(user_data.password)

    activation_code = f"{secrets.randbelow(900000) + 100000:06d}"

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_pwd,
        email_confirmed=False,
        confirmation_code=_make_confirmation_record(activation_code),
    )

    db.add(new_user)
    await db.commit()

    background_tasks.add_task(send_confirmation_code, user_data.email, activation_code)

    return {"message": "User created", "email": user_data.email}


@router.post("/verify-email")
async def verify_email_code(data: VerifyEmailRequest, db: db_dependency):
    query = select(User).where(User.email == data.email)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if user.email_confirmed:
        return {"message": "Почта уже подтверждена"}

    confirmation_record = _parse_confirmation_record(user.confirmation_code)
    if not confirmation_record:
        raise HTTPException(status_code=400, detail="Код недействителен. Запросите новый код.")

    code_hash, expires_at, attempts = confirmation_record

    if datetime.utcnow().timestamp() > expires_at:
        raise HTTPException(status_code=400, detail="Срок действия кода истек")

    if attempts >= CONFIRMATION_CODE_MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Слишком много попыток. Запросите новый код.")

    if hmac.compare_digest(code_hash, hash_confirmation_code(data.code)):
        user.email_confirmed = True
        user.confirmation_code = None
        await db.commit()
        return {"message": "Успех"}

    user.confirmation_code = f"{code_hash}:{expires_at}:{attempts + 1}"
    await db.commit()
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
            status_code=403, detail="Почта не подтверждена. Введите код, отправленный на email."
        )

    access_token = create_access_token(data={"sub": user.username})
    response = JSONResponse(content={"status": "ok", "username": user.username})
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return response


@router.post("/logout")
async def logout():
    response = JSONResponse(content={"message": "Вы успешно вышли"})
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )
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
        raise HTTPException(status_code=401, detail="Ошибка авторизации") from None

    query = select(User).where(User.username == username)
    result = await db.execute(query)
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user
