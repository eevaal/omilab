from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from core.security import get_password_hash, verify_password
from database.dependencies import db_dependency
from models.users import User
from schemas.users import UserResponse, UserCreate

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
async def login(user_data: UserCreate, db: db_dependency):
    # 1. Ищем юзера
    query = select(User).where(User.username == user_data.username)
    result = await db.execute(query)
    user = result.scalars().first()

    # 2. Проверяем существование и пароль
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")

    # В будущем здесь будем выдавать Token, сейчас просто пускаем
    return {"status": "ok", "message": "Успешный вход"}