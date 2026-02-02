from core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    decode_access_token,
)
from database.dependencies import db_dependency
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from models.users import User
from schemas.users import UserCreate, UserLogin, UserResponse
from sqlalchemy import select

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: db_dependency):
    q_username = select(User).where(User.username == user_data.username)
    result_username = await db.execute(q_username)
    existing_user = result_username.scalars().first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с данным именем уже существует")

    q_email = select(User).where(User.email == user_data.email)
    result_email = await db.execute(q_email)
    existing_email = result_email.scalars().first()

    if existing_email:
        raise HTTPException(status_code=400, detail="Пользователь с данным email уже существует")

    hashed_pwd = get_password_hash(user_data.password)

    new_user = User(username=user_data.username, email=user_data.email, hashed_password=hashed_pwd)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/login")
async def login(user_data: UserLogin, db: db_dependency):
    query = select(User).where(User.username == user_data.username)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверные данные")

    access_token = create_access_token(data={"sub": user.username})

    response = JSONResponse(content={"status": "ok", "username": user.username})

    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        path="/",
    )

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

        if username is None:
            raise HTTPException(status_code=401, detail="Неверный токен")

    except Exception:
        raise HTTPException(status_code=401, detail="Ошибка авторизации")

    query = select(User).where(User.username == username)
    result = await db.execute(query)
    user = result.scalars().first()

    if user is None:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    return user
