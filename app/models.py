from typing import Optional

from pydantic import BaseModel, EmailStr

class User(BaseModel):
    """Модель пользователя, представляющая пользователя в системе."""
    username: str
    email: EmailStr
    hashed_password: str
    is_active: bool = False

class UserInDB(User):
    """Модель пользователя с дополнительным полем ID для хранения в базе данных."""
    id: int

class Token(BaseModel):
    """Модель токена, представляющая токен доступа."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Модель данных токена, представляющая данные внутри токена."""
    username: Optional[str] = None
