from typing import Any, Dict

from bson import ObjectId
from fastapi.exceptions import HTTPException
from pymongo.results import UpdateResult

from app.database import users

async def create_task_group(user: dict[str, Any], group_name: str):
    """
    Создает новую группу задач с автоматически увеличенным order_num.
    Возвращает результат обновления MongoDB.

    Args:
        user (dict[str, Any]): Информация о пользователе.
        group_name (str): Название новой группы задач.

    Returns:
        dict: Результат операции с идентификатором созданной группы задач.

    Raises:
        HTTPException: Если имя группы не является строкой или уже существует.
    """
    if not group_name or not isinstance(group_name, str):
        raise HTTPException(status_code=400, detail="Group name must be a non-empty string")

    if get_task_group(user, group_name) is not None:
        raise HTTPException(status_code=409, detail=f"Task group '{group_name}' already exists")

    new_group_id = ObjectId()

    user_doc = await users.find_one({"_id": user["_id"]}, {"todo.order_num": 1})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    max_order_num = max([t.get("order_num", 0) for t in user_doc.get("todo", [])] or [0])
    new_order_num = max_order_num + 1

    result: UpdateResult = await users.update_one(
        {"_id": user["_id"]},
        {
            "$push": {
                "todo": {
                    "_id": new_group_id,
                    "title": group_name,
                    "order_num": new_order_num,
                    "tasks": []
                }
            }
        }
    )

    if result.modified_count == 1:
        return {"Result": "success", "task_group_id": str(new_group_id)}
    else:
        raise HTTPException(status_code=500, detail="Failed to create task group")

def get_task(task_group: dict[str, Any], task_name: str) -> dict[str, Any]:
    """
    Получает задачу из группы задач по названию.

    Args:
        task_group (dict[str, Any]): Группа задач.
        task_name (str): Название задачи.

    Returns:
        dict[str, Any]: Задача, если найдена, иначе None.
    """
    for task in task_group["tasks"]:
        if task["title"] == task_name:
            return task
    return None

def get_task_group(user, group_name):
    """
    Получает группу задач пользователя по названию.

    Args:
        user (dict[str, Any]): Информация о пользователе.
        group_name (str): Название группы задач.

    Returns:
        dict[str, Any]: Группа задач, если найдена, иначе None.
    """
    for group in user["todo"]:
        if group["title"] == group_name:
            return group
    return None

async def delete_task_group(user: dict[str, Any], group_name: str) -> Dict[str, str]:
    """
    Удаляет группу задач по названию и обновляет порядковые номера оставшихся групп.
    Возвращает сообщение об успехе или выбрасывает соответствующее исключение HTTPException.

    Args:
        user (dict[str, Any]): Информация о пользователе.
        group_name (str): Название группы задач для удаления.

    Returns:
        dict: Сообщение об успешном удалении.

    Raises:
        HTTPException: Если группа не найдена или операция не удалась.
    """
    try:
        user_doc = await users.find_one(
            {"_id": user["_id"], "todo.title": group_name},
            {"todo.$": 1}
        )

        if not user_doc or not user_doc.get("todo"):
            raise HTTPException(status_code=404, detail="Group not found")

        deleted_order = user_doc["todo"][0]["order_num"]

        delete_result = await users.update_one(
            {"_id": user["_id"]},
            {"$pull": {"todo": {"title": group_name}}}
        )

        if delete_result.modified_count != 1:
            raise HTTPException(status_code=404, detail="Group not found or already deleted")

        user_groups = await users.find_one({"_id": user["_id"]}, {"todo": 1})

        updated_todo = []
        for group in user_groups["todo"]:
            if group["order_num"] > deleted_order:
                group["order_num"] -= 1
            updated_todo.append(group)

        update_result = await users.update_one(
            {"_id": user["_id"]},
            {"$set": {"todo": updated_todo}}
        )

        if update_result.modified_count == 1:
            return {"Result": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update task groups order")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database operation failed: {str(e)}")

async def rename_task_group(user: dict[str, Any], old_group_name: str, new_group_name: str) -> Dict[str, str]:
    """
    Переименовывает группу задач, обеспечивая:
    - Существование старой группы
    - Новое имя не занято
    - Корректная обработка ошибок

    Args:
        user (dict[str, Any]): Информация о пользователе.
        old_group_name (str): Текущее название группы задач.
        new_group_name (str): Новое название группы задач.

    Returns:
        dict: Сообщение об успешном переименовании.

    Raises:
        HTTPException: Если имена пустые, совпадают или операция не удалась.
    """
    if not old_group_name or not new_group_name:
        raise HTTPException(status_code=400, detail="Group names cannot be empty")
    if old_group_name == new_group_name:
        raise HTTPException(status_code=400, detail="New name must be different from old name")

    try:
        existing_group = await users.find_one({
            "_id": user["_id"],
            "todo.title": new_group_name
        })

        if existing_group:
            raise HTTPException(status_code=409, detail=f"Group '{new_group_name}' already exists")

        result = await users.update_one(
            {"_id": user["_id"], "todo.title": old_group_name},
            {"$set": {"todo.$.title": new_group_name}}
        )

        if result.modified_count == 1:
            return {"Result": "success"}
        else:
            raise HTTPException(status_code=404, detail=f"Group '{old_group_name}' not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

async def create_task(user: dict[str, Any], group_name: str, task_name: str, description: str) -> Dict[str, str]:
    """
    Создает новую задачу в указанной группе задач.

    Args:
        user (dict[str, Any]): Информация о пользователе.
        group_name (str): Название группы задач.
        task_name (str): Название задачи.
        description (str): Описание задачи.

    Returns:
        dict: Сообщение об успешном создании задачи с идентификатором задачи.

    Raises:
        HTTPException: Если название задачи не является строкой или задача уже существует.
    """
    if not task_name or not isinstance(task_name, str):
        raise HTTPException(status_code=400, detail="Task name must be a non-empty string")

    group = get_task_group(user, group_name)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")

    if get_task(group, task_name) is not None:
        raise HTTPException(status_code=409, detail=f"Task '{task_name}' already exists")

    new_task_id = ObjectId()

    new_order_num = max(t["order_num"] for t in group["tasks"]) + 1 if group["tasks"] else 1

    result: UpdateResult = await users.update_one(
        {"_id": user["_id"], "todo.title": group_name},
        {
            "$push": {
                "todo.$.tasks": {
                    "_id": new_task_id,
                    "title": task_name,
                    "description": description,
                    "order_num": new_order_num,
                }
            }
        }
    )

    if result.modified_count == 1:
        return {"Result": "success", "task_id": str(new_task_id)}
    else:
        raise HTTPException(status_code=500, detail="Failed to create task")

async def delete_task(user: dict[str, Any], group_name: str, task_name: str) -> Dict[str, str]:
    """
    Удаляет задачу из указанной группы задач и обновляет порядковые номера оставшихся задач.

    Args:
        user (dict[str, Any]): Информация о пользователе.
        group_name (str): Название группы задач.
        task_name (str): Название задачи для удаления.

    Returns:
        dict: Сообщение об успешном удалении задачи.

    Raises:
        HTTPException: Если группа или задача не найдены или операция не удалась.
    """
    task_group = get_task_group(user, group_name)
    if task_group is None:
        raise HTTPException(status_code=404, detail="Group not found")

    task_to_delete = get_task(task_group, task_name)
    if task_to_delete is None:
        raise HTTPException(status_code=404, detail="Task not found")

    result = await users.update_one(
        {"_id": user["_id"], "todo.title": group_name},
        {"$pull": {"todo.$.tasks": {"title": task_name}}}
    )

    if result.modified_count == 1:
        updated_tasks = []
        for task in task_group["tasks"]:
            if task["title"] != task_name:
                if task["order_num"] > task_to_delete["order_num"]:
                    task["order_num"] -= 1
                updated_tasks.append(task)

        update_result = await users.update_one(
            {"_id": user["_id"], "todo.title": group_name},
            {"$set": {"todo.$.tasks": updated_tasks}}
        )

        if update_result.modified_count == 1:
            return {"Result": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update tasks order")
    else:
        raise HTTPException(status_code=500, detail="Failed to delete task")
