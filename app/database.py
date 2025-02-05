import os

from dotenv import load_dotenv
from pymongo import AsyncMongoClient

load_dotenv()

client = AsyncMongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
db = client.todo_db
users = db.users


async def on_init():  # fixme функция никогда не вызывается
    await users.create_index("username", unique=True)
    await users.create_index("email", unique=True)


async def get_user_by_username(username: str):
    return await users.find_one({"username": username})


async def get_user_by_email(email: str):
    return await users.find_one({"email": email})


async def add_user(username, email, hashed_password):
    await users.insert_one(
        dict(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=False,
            todo=dict(),
        )
    )


async def activate_user(email):
    await users.update_one({"email": email}, {"$set": {"is_active": True}})


async def update_password(email, password):
    await users.update_one({"email": email}, {"$set": {"hashed_password": password}})
