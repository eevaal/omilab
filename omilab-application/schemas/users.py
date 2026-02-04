from typing import Optional

from pydantic import BaseModel, EmailStr, validator


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    is_verified: bool

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    email: str
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    password_confirm: Optional[str] = None

    @validator('password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        # Если пароль задан, а подтверждение не совпадает — ошибка
        if 'password' in values and values['password'] and v != values['password']:
            raise ValueError('Пароли не совпадают')
        return v
