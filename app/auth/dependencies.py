from fastapi import Depends, HTTPException

from app.database import get_user_by_username
from .constants import oauth2_scheme
from .services import decode_token

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Получает текущего пользователя на основе токена.

    Args:
        token (str): Токен доступа для аутентификации пользователя.

    Returns:
        dict: Информация о пользователе.

    Raises:
        HTTPException: Если пользователь не найден.
    """
    username = decode_token(token)
    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
