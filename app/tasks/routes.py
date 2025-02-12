from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_user
from . import models, crud

tasks_router = APIRouter(prefix="/task-groups", tags=["tasks"])


@tasks_router.post("/{group_name}",
                   # response_model=models.TaskGroupCreate
                   )
async def create_group(
        group_name: str,
        user=Depends(get_current_user)
):
    """Creates group of tasks."""
    new_group = await crud.create_task_group(user, group_name)
    return new_group
    # return TaskGroupOut(group_name=group_name, tasks=new_group[group_name], )


@tasks_router.get("/",
                  response_model=list[models.GetTaskGroup]
                  )
async def get_task_groups(user=Depends(get_current_user)):
    """Returns all groups of tasks."""
    return user["todo"]


@tasks_router.get("/{group_name}",
                  response_model=models.GetTaskGroup
                  )
async def get_group(
        group_name: str,
        user=Depends(get_current_user)
):
    """Returns needed group of tasks by its title (`group_name`)."""
    group = crud.get_task_group(user, group_name)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@tasks_router.put("/{group_name}", response_model=dict)
async def rename_group(group_name: str, new_group_name: str, user=Depends(get_current_user)):
    """Replaces current title of group of tasks (`group_name`) with new group name (`new_group_name`)."""
    return await crud.rename_task_group(user, group_name, new_group_name)


# @tasks_router.get("/{group_name}")
# async def get_group_name(group_name: str, user=Depends(get_current_user)):
#     crud.


# @tasks_router.put("/{group_name}",
#                   # response_model=models.TaskGroupOut
#                   )
# async def update_group_name(
#         group_name: str,
#         new_group_name: str,
#         # group_data: models.TaskGroupUpdate,
#         user=Depends(get_current_user)
# ):
#     # db_user = users.find_one({"username": user["username"]})
#     updated_group = await crud.update_task_group(db_user, group_id, group_data)
#     if not updated_group:
#         raise HTTPException(status_code=404, detail="Group not found")
#     return updated_group
#
#
@tasks_router.delete("/{group_name}")
async def delete_group(
        group_name: str,
        user=Depends(get_current_user)
):
    """Deletes group of tasks by its title (`group_name`)."""
    result = await crud.delete_task_group(user, group_name)
    return result


@tasks_router.post("/{group_name}/{task_name}")
async def create_task(group_name: str, task_name: str, description: str = "", user=Depends(get_current_user)):
    """Creates task with title `task_name` and `description` in group with `group_name` title."""
    return await crud.create_task(user, group_name, task_name, description)


@tasks_router.get("/{group_name}/{task_name}", response_model=models.Task)
def get_task(group_name: str, task_name: str, user=Depends(get_current_user)):
    """Returns task with title `task_name` in group with `group_name` title."""
    task_group = crud.get_task_group(user, group_name)
    return crud.get_task(task_group, task_name)


@tasks_router.delete("/{group_name}/{task_name}")
async def delete_task(group_name: str, task_name: str, user=Depends(get_current_user)) :
    """Deletes task with title `task_name` from group with `group_name` title."""
    return await crud.delete_task(user, group_name, task_name)

# @tasks_router.post("/{group_id}/tasks", response_model=models.TaskOut)
# async def create_task(
#         group_id: str,
#         task_data: models.TaskCreate,
#         user=Depends(get_current_user)
# ):
#     db_user = users.find_one({"username": user["username"]})
#     new_task = await crud.create_task(db_user, group_id, task_data)
#     if not new_task:
#         raise HTTPException(status_code=404, detail="Group not found")
#     return new_task

#
# @tasks_router.put("/{group_id}/tasks/{task_id}", response_model=models.TaskOut)
# async def update_task(
#         group_id: str,
#         task_id: str,
#         task_data: models.TaskUpdate,
#         user=Depends(get_current_user)
# ):
#     db_user = users.find_one({"username": user["username"]})
#     success = await crud.update_task(db_user, group_id, task_id, task_data)
#     if not success:
#         raise HTTPException(status_code=404, detail="Task not found")
#     return await crud.get_task(db_user, group_id, task_id)
#
#
# @tasks_router.delete("/{group_id}/tasks/{task_id}")
# async def delete_task(
#         group_id: str,
#         task_id: str,
#         user=Depends(get_current_user)
# ):
#     db_user = users.find_one({"username": user["username"]})
#     success = await crud.delete_task(db_user, group_id, task_id)
#     if not success:
#         raise HTTPException(status_code=404, detail="Task not found")
#     return {"message": "Task deleted successfully"}
