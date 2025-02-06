from fastapi import FastAPI, Depends

from app.auth.dependencies import get_current_user
from app.auth.router import auth_router
from app.tasks.routes import tasks_router
from app.models import User
app = FastAPI()

app.include_router(auth_router)
app.include_router(tasks_router)


@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user["username"]}
