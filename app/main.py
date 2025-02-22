import os
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import EmailStr

from app.database import get_user_by_username, get_user_by_email, add_user, activate_user
from app.models import Token, User
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()
MAIL = os.getenv("MAIL")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")

if not MAIL or not MAIL_PASSWORD or not SMTP_SERVER:
    raise Exception(f"SET ALL .env variables, {MAIL=}, {MAIL_PASSWORD=}, {SMTP_SERVER=}")

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
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


def authenticate_user(username: str, password: str) -> tuple[int, str, str, str, int] | bool:
    user = get_user_by_username(username)
    if not user or not verify_password(password, user[3]):
        return False
    return user


def send_confirmation_email(email: EmailStr, token: str):
    msg = MIMEText(f"Click the link to confirm your email: http://127.0.0.1:8050/confirm?token={token}")
    msg["Subject"] = "Confirm your email"
    msg["From"] = MAIL
    msg["To"] = email

    with smtplib.SMTP_SSL(SMTP_SERVER, 465) as server:
        server.login(MAIL.split("@")[0], MAIL_PASSWORD)
        server.sendmail(MAIL, [str(email)], msg.as_string())


def create_confirmation_token(email: EmailStr):
    expires_delta = timedelta(hours=24)
    return create_access_token(data={"sub": email}, expires_delta=expires_delta)


@app.get("/confirm")
async def confirm_email(token: str):
    email = decode_token(token)
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    activate_user(email)

    return {"message": "Email confirmed"}


@app.post("/token", response_model=Token)
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user or not verify_password(form_data.password, user[3]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not user[-1]:
        raise HTTPException(status_code=400, detail="Account not activated")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user[1]}, expires_delta=access_token_expires
    )
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(token: str = Depends(oauth2_scheme)):
    username = decode_token(token)
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/register")
async def register(username: str, email: EmailStr, password: str):
    if get_user_by_username(username):
        raise HTTPException(status_code=400, detail="Username already registered")
    if get_user_by_email(email):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(password)

    add_user(username, email, hashed_password)

    confirmation_token = create_confirmation_token(email)

    send_confirmation_email(email, confirmation_token)

    return {"message": "User registered. Please check your email to confirm your account."}
