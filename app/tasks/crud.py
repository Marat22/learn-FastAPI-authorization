# app/tasks/crud.py
import uuid
from datetime import datetime
from typing import Any

from bson import ObjectId
from fastapi.exceptions import HTTPException

from app.database import users

from pymongo.results import UpdateResult

# Helper functions
# async def get_todo_structure(user) -> :
#     # if "todo" not in user:
#     #     await users.update_one(
#     #         {"_id": user["_id"]},
#     #         {"$set": {"todo": {}}}
#     #     )
#     return user["todo"]


# Task Group CRUD
async def create_task_group(user: dict[str, Any], group_name: str):
    """
    Creates a new task group with auto-incremented order_num.
    Returns MongoDB UpdateResult.
    """
    # Validate input
    if not group_name or not isinstance(group_name, str):
        raise HTTPException(status_code=400, detail="Group name must be a non-empty string")

    # Check if group already exists
    if get_task_group(user, group_name) is not None:
        raise HTTPException(status_code=409, detail=f"Task group '{group_name}' already exists")

    # Generate new ObjectId for the task group
    new_group_id = ObjectId()

    # Step 1: Find the current maximum order_num
    user_doc = await users.find_one({"_id": user["_id"]}, {"todo.order_num": 1})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    # Calculate the new order_num
    max_order_num = max([t.get("order_num", 0) for t in user_doc.get("todo", [])] or [0])
    new_order_num = max_order_num + 1

    # Step 2: Add the new task group using $push
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

    # Check if the update was successful
    if result.modified_count == 1:
        return {"Result": "success", "task_group_id": str(new_group_id)}
    else:
        raise HTTPException(status_code=500, detail="Failed to create task group")

def get_task_group(user, group_name):
    return next(
        (g for g in user["todo"] if g["title"] == group_name),
        None
    )


async def update_task_group(user: dict[str, Any], group_id, group_data):
    update_data = {
        f"todo.task_groups.$.{k}": v
        for k, v in group_data.dict(exclude_unset=True).items()
    }
    update_data["todo.task_groups.$.updated_at"] = datetime.now()

    result = await users.update_one(
        {"_id": user["_id"], "todo.task_groups._id": group_id},
        {"$set": update_data}
    )
    if result.modified_count == 0:
        return None
    return await get_task_group(user, group_id)


async def delete_task_group(user, group_id):
    result = await users.update_one(
        {"_id": user["_id"]},
        {"$pull": {"todo.task_groups": {"_id": group_id}}}
    )
    return result.modified_count > 0


# Task CRUD
async def create_task(user, group_id, task_data):
    task_id = str(uuid.uuid4())
    new_task = {
        "_id": task_id,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        **task_data.dict()
    }

    result = await  users.update_one(
        {"_id": user["_id"], "todo.task_groups._id": group_id},
        {"$push": {"todo.task_groups.$.tasks": new_task}}
    )
    if result.modified_count == 0:
        return None
    return new_task


async def get_task(user, group_id, task_id):
    group = await get_task_group(user, group_id)
    if not group:
        return None
    return next((t for t in group["tasks"] if t["_id"] == task_id), None)


async def update_task(user, group_id, task_id, task_data):
    update_data = {
        f"todo.task_groups.$[group].tasks.$[task].{k}": v
        for k, v in task_data.dict(exclude_unset=True).items()
    }
    update_data["todo.task_groups.$[group].tasks.$[task].updated_at"] = datetime.now()

    result = await users.update_one(
        {"_id": user["_id"], "todo.task_groups._id": group_id},
        {"$set": update_data},
        array_filters=[
            {"group._id": group_id},
            {"task._id": task_id}
        ]
    )
    return result.modified_count > 0


async def delete_task(user, group_id, task_id):
    result = await users.update_one(
        {"_id": user["_id"], "todo.task_groups._id": group_id},
        {"$pull": {"todo.task_groups.$.tasks": {"_id": task_id}}}
    )
    return result.modified_count > 0
