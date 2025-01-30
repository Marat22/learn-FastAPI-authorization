from typing import Optional

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    username: str
    email: EmailStr
    hashed_password: str
    is_active: bool = False


class UserInDB(User):
    id: int


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
