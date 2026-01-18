from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from core.security import get_password_hash
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