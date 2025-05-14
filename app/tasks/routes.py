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
    """Создает группу задач.

    Args:
        group_name (str): Название группы задач.
        user (dict): Текущий пользователь.

    Returns:
        dict: Результат создания группы задач.
    """
    new_group = await crud.create_task_group(user, group_name)
    return new_group

@tasks_router.get("/",
                  response_model=list[models.GetTaskGroup]
                  )
async def get_task_groups(user=Depends(get_current_user)):
    """Возвращает все группы задач пользователя.

    Args:
        user (dict): Текущий пользователь.

    Returns:
        list[models.GetTaskGroup]: Список групп задач.
    """
    return user["todo"]

@tasks_router.get("/{group_name}",
                  response_model=models.GetTaskGroup
                  )
async def get_group(
        group_name: str,
        user=Depends(get_current_user)
):
    """Возвращает нужную группу задач по ее названию.

    Args:
        group_name (str): Название группы задач.
        user (dict): Текущий пользователь.

    Returns:
        models.GetTaskGroup: Группа задач.

    Raises:
        HTTPException: Если группа не найдена.
    """
    group = crud.get_task_group(user, group_name)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return group

@tasks_router.put("/{group_name}", response_model=dict)
async def rename_group(group_name: str, new_group_name: str, user=Depends(get_current_user)):
    """Заменяет текущее название группы задач на новое.

    Args:
        group_name (str): Текущее название группы задач.
        new_group_name (str): Новое название группы задач.
        user (dict): Текущий пользователь.

    Returns:
        dict: Результат переименования группы задач.
    """
    return await crud.rename_task_group(user, group_name, new_group_name)

@tasks_router.delete("/{group_name}")
async def delete_group(
        group_name: str,
        user=Depends(get_current_user)
):
    """Удаляет группу задач по ее названию.

    Args:
        group_name (str): Название группы задач.
        user (dict): Текущий пользователь.

    Returns:
        dict: Результат удаления группы задач.
    """
    result = await crud.delete_task_group(user, group_name)
    return result

@tasks_router.post("/{group_name}/{task_name}")
async def create_task(group_name: str, task_name: str, description: str = "", user=Depends(get_current_user)):
    """Создает задачу с названием и описанием в указанной группе задач.

    Args:
        group_name (str): Название группы задач.
        task_name (str): Название задачи.
        description (str): Описание задачи.
        user (dict): Текущий пользователь.

    Returns:
        dict: Результат создания задачи.
    """
    return await crud.create_task(user, group_name, task_name, description)

@tasks_router.get("/{group_name}/{task_name}", response_model=models.Task)
def get_task(group_name: str, task_name: str, user=Depends(get_current_user)):
    """Возвращает задачу по ее названию в указанной группе задач.

    Args:
        group_name (str): Название группы задач.
        task_name (str): Название задачи.
        user (dict): Текущий пользователь.

    Returns:
        models.Task: Задача.

    Raises:
        HTTPException: Если задача не найдена.
    """
    task_group = crud.get_task_group(user, group_name)
    if task_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    task = crud.get_task(task_group, task_name)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@tasks_router.delete("/{group_name}/{task_name}")
async def delete_task(group_name: str, task_name: str, user=Depends(get_current_user)):
    """Удаляет задачу по ее названию из указанной группы задач.

    Args:
        group_name (str): Название группы задач.
        task_name (str): Название задачи.
        user (dict): Текущий пользователь.

    Returns:
        dict: Результат удаления задачи.
    """
    return await crud.delete_task(user, group_name, task_name)
