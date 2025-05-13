from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends

from app.auth.dependencies import get_current_user
from app.auth.router import auth_router
from app.database import on_init
from app.models import User
from app.tasks.routes import tasks_router

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Инициализирует приложение с индексами базы данных."""
    await on_init()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(tasks_router)

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Получает информацию о текущем пользователе.

    Args:
        current_user (User): Текущий пользователь.

    Returns:
        dict: Имя пользователя текущего пользователя.
    """
    return {"username": current_user["username"]}
