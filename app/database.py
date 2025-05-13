import os

from dotenv import load_dotenv
from pymongo import AsyncMongoClient

load_dotenv()

client = AsyncMongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
db = client.todo_db
users = db.users

async def on_init():
    """Инициализирует индексы для коллекции пользователей в базе данных."""
    await users.create_index("username", unique=True)
    await users.create_index("email", unique=True)

async def get_user_by_username(username: str):
    """Получает пользователя по имени пользователя.

    Args:
        username (str): Имя пользователя для поиска.

    Returns:
        dict: Документ пользователя, если найден, иначе None.
    """
    return await users.find_one({"username": username})

async def get_user_by_email(email: str):
    """Получает пользователя по электронной почте.

    Args:
        email (str): Электронная почта для поиска.

    Returns:
        dict: Документ пользователя, если найден, иначе None.
    """
    return await users.find_one({"email": email})

async def add_user(username, email, hashed_password):
    """Добавляет нового пользователя в базу данных.

    Args:
        username (str): Имя пользователя.
        email (str): Электронная почта пользователя.
        hashed_password (str): Хешированный пароль пользователя.
    """
    await users.insert_one(
        dict(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=False,
            todo=[],
        )
    )

async def activate_user(email):
    """Активирует пользователя, устанавливая флаг is_active в True.

    Args:
        email (str): Электронная почта пользователя для активации.
    """
    await users.update_one({"email": email}, {"$set": {"is_active": True}})

async def update_password(email, password):
    """Обновляет пароль пользователя.

    Args:
        email (str): Электронная почта пользователя для обновления.
        password (str): Новый хешированный пароль.
    """
    await users.update_one({"email": email}, {"$set": {"hashed_password": password}})
