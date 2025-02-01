import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
db = client.todo_db
users = db.users
users.create_index("username", unique=True)
users.create_index("email", unique=True)


def get_user_by_username(username: str):
    return users.find_one({"username": username})


def get_user_by_email(email: str):
    return users.find_one({"email": email})


def add_user(username, email, hashed_password):
    users.insert_one(
        dict(
            username=username,
            email=email,
            hashed_password=hashed_password,
            is_active=False,
            todo=dict(),
        )
    )


def activate_user(email):
    users.update_one({"email": email}, {"$set": {"is_active": True}})
