from datetime import datetime, timedelta, UTC
from typing import Optional

from fastapi import HTTPException
from jose import JWTError, jwt
from pydantic import EmailStr

from app.database import get_user_by_username
from .constants import pwd_context, SECRET_KEY, ALGORITHM


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def authenticate_user(username: str, password: str) -> dict | bool:
    user = await get_user_by_username(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user


def create_confirmation_token(email: EmailStr):
    expires_delta = timedelta(hours=24)
    return create_access_token(data={"sub": email}, expires_delta=expires_delta)


def create_password_reset_token(email: EmailStr):
    expires_delta = timedelta(minutes=15)
    return create_access_token(
        data={"sub": email, "type": "password_reset"},  # Add type distinction
        expires_delta=expires_delta
    )


def verify_password_reset_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")

        if not email or token_type != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token type")

        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
