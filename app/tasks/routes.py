from fastapi import APIRouter, Depends, HTTPException, Form

from app.auth.dependencies import get_current_user
from app.database import users
from . import models, crud
from .models import TaskGroupOut

tasks_router = APIRouter(prefix="/task-groups", tags=["tasks"])


@tasks_router.post("/",
                   # response_model=models.TaskGroupOut
                   )
async def create_group(
    group_name: str,
    user=Depends(get_current_user)
):
    new_group = await crud.create_task_group(user, group_name)
    return new_group
    # return TaskGroupOut(group_name=group_name, tasks=new_group[group_name], )


@tasks_router.get("/", response_model=list[models.TaskGroupOut])
async def get_task_groups(user=Depends(get_current_user)):
    db_user = users.find_one({"username": user["username"]})
    return db_user["todo"]


@tasks_router.get("/{group_id}", response_model=models.TaskGroupOut)
async def get_group(
        group_id: str,
        user=Depends(get_current_user)
):
    db_user = users.find_one({"username": user["username"]})
    group = await crud.get_task_group(db_user, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@tasks_router.put("/{group_id}", response_model=models.TaskGroupOut)
async def update_group(
        group_id: str,
        group_data: models.TaskGroupUpdate,
        user=Depends(get_current_user)
):
    db_user = users.find_one({"username": user["username"]})
    updated_group = await crud.update_task_group(db_user, group_id, group_data)
    if not updated_group:
        raise HTTPException(status_code=404, detail="Group not found")
    return updated_group


@tasks_router.delete("/{group_id}")
async def delete_group(
        group_id: str,
        user=Depends(get_current_user)
):
    db_user = users.find_one({"username": user["username"]})
    success = await crud.delete_task_group(db_user, group_id)
    if not success:
        raise HTTPException(status_code=404, detail="Group not found")
    return {"message": "Group deleted successfully"}


@tasks_router.post("/{group_id}/tasks", response_model=models.TaskOut)
async def create_task(
        group_id: str,
        task_data: models.TaskCreate,
        user=Depends(get_current_user)
):
    db_user = users.find_one({"username": user["username"]})
    new_task = await crud.create_task(db_user, group_id, task_data)
    if not new_task:
        raise HTTPException(status_code=404, detail="Group not found")
    return new_task


@tasks_router.put("/{group_id}/tasks/{task_id}", response_model=models.TaskOut)
async def update_task(
        group_id: str,
        task_id: str,
        task_data: models.TaskUpdate,
        user=Depends(get_current_user)
):
    db_user = users.find_one({"username": user["username"]})
    success = await crud.update_task(db_user, group_id, task_id, task_data)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return await crud.get_task(db_user, group_id, task_id)


@tasks_router.delete("/{group_id}/tasks/{task_id}")
async def delete_task(
        group_id: str,
        task_id: str,
        user=Depends(get_current_user)
):
    db_user = users.find_one({"username": user["username"]})
    success = await crud.delete_task(db_user, group_id, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}
