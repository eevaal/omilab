from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_]+$")
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserResponse(UserBase):
    id: int
    is_verified: bool

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    password_confirm: str | None = Field(default=None, min_length=8, max_length=128)

    @validator("password_confirm")
    def passwords_match(cls, v, values, **kwargs):
        # Если пароль задан, а подтверждение не совпадает — ошибка
        if "password" in values and values["password"] and v != values["password"]:
            raise ValueError("Пароли не совпадают")
        return v
