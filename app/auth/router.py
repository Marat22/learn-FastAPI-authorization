from datetime import timedelta

from fastapi import APIRouter
from fastapi import Depends, HTTPException, Response
from fastapi import Form
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr

from app.database import get_user_by_username, get_user_by_email, add_user, activate_user, update_password
from app.email import send_update_password_email, send_confirmation_email
from app.models import Token
from .constants import ACCESS_TOKEN_EXPIRE_MINUTES
from .services import decode_token, authenticate_user, verify_password, create_access_token, create_confirmation_token, \
    get_password_hash, verify_password_reset_token, create_password_reset_token

auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.post("/register")
async def register(request: Request, username: str, email: EmailStr, password: str):
    """Регистрирует нового пользователя.

    Args:
        request (Request): Объект запроса.
        username (str): Имя пользователя.
        email (EmailStr): Электронная почта пользователя.
        password (str): Пароль пользователя.

    Returns:
        dict: Сообщение об успешной регистрации.

    Raises:
        HTTPException: Если имя пользователя или электронная почта уже зарегистрированы.
    """
    if await get_user_by_username(username):
        raise HTTPException(status_code=400, detail="Username already registered")
    if await get_user_by_email(email):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(password)
    await add_user(username, email, hashed_password)
    confirmation_token = create_confirmation_token(email)
    send_confirmation_email(email, f"{request.base_url}auth/confirm?token={confirmation_token}")

    return {"message": "User registered. Please check your email to confirm your account."}

@auth_router.get("/confirm")
async def confirm_email(token: str):
    """Подтверждает электронную почту во время регистрации.

    Args:
        token (str): Токен подтверждения.

    Returns:
        dict: Сообщение об успешном подтверждении.

    Raises:
        HTTPException: Если пользователь не найден.
    """
    email = decode_token(token)
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await activate_user(email)

    return {"message": "Email confirmed"}

@auth_router.post("/token", response_model=Token)
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    """Проверяет пароль и устанавливает токен доступа в cookies.

    Args:
        response (Response): Объект ответа.
        form_data (OAuth2PasswordRequestForm): Данные формы для аутентификации.

    Returns:
        dict: Токен доступа.

    Raises:
        HTTPException: Если имя пользователя или пароль неверны, или аккаунт не активирован.
    """
    user = await authenticate_user(form_data.username, form_data.password)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not user["is_active"]:
        raise HTTPException(status_code=400, detail="Account not activated")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.post("/forgot-password")
async def forgot_password(request: Request, email: EmailStr):
    """Отправляет URL для сброса пароля на указанную электронную почту.

    Args:
        request (Request): Объект запроса.
        email (EmailStr): Электронная почта пользователя.

    Returns:
        dict: Сообщение об отправке ссылки для сброса пароля.

    Raises:
        HTTPException: Если пользователь не найден.
    """
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    reset_token = create_password_reset_token(email)

    # Use your actual frontend URL here
    reset_url = f"{request.base_url}auth/reset-password?token={reset_token}"

    send_update_password_email(email, reset_url)
    return {"message": "Password reset link sent to your email"}

@auth_router.post("/reset-password")
async def reset_password(
        token: str = Form(...),
        new_password: str = Form(...)
):
    """Устанавливает новый пароль.

    Args:
        token (str): Токен для сброса пароля.
        new_password (str): Новый пароль.

    Returns:
        dict: Сообщение об успешном обновлении пароля.

    Raises:
        HTTPException: Если пользователь не найден.
    """
    email = verify_password_reset_token(token)
    user = await get_user_by_email(email)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update password in database
    await update_password(email, get_password_hash(new_password))

    return {"message": "Password updated successfully"}

@auth_router.get("/reset-password")
def show_reset_form(token: str):
    """Возвращает HTML страницу для сброса пароля.

    Args:
        token (str): Токен для сброса пароля.

    Returns:
        HTMLResponse: HTML форма для сброса пароля или сообщение об ошибке.
    """
    # Verify token first
    try:
        verify_password_reset_token(token)
    except HTTPException:
        return HTMLResponse("Invalid or expired token")

    return HTMLResponse(f"""
        <form action="/auth/reset-password" method="post">
            <input type="hidden" name="token" value="{token}">
            <input type="password" name="new_password" required>
            <button type="submit">Reset Password</button>
        </form>
    """)
