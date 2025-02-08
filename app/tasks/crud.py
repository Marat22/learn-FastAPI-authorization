# app/tasks/crud.py
import uuid
from datetime import datetime
from typing import Any

from bson import ObjectId
from fastapi.exceptions import HTTPException

from app.database import users


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
    if get_task_group(user, group_name) is not None:
        raise HTTPException(status_code=409, detail=f"{group_name} already exists.")

    new_group_id = ObjectId()

    # Correct aggregation pipeline for update
    pipeline = [
        {
            "$set": {
                "new_order": {
                    "$add": [
                        {"$ifNull": [{"$max": "$todo.order_num"}, 0]},
                        1
                    ]
                }
            }
        },
        {
            "$set": {
                "todo": {
                    "$concatArrays": [
                        "$todo",
                        [{
                            "_id": new_group_id,
                            "title": group_name,
                            "order_num": "$new_order",
                            "tasks": []
                        }]
                    ]
                }
            }
        }
    ]

    result = await users.update_one(
        {"_id": user["_id"]},
        pipeline
    )

    return {"Result": "success"}
    # await users.update_one(
    #     {"_id": user["_id"]},
    #     {"$set": {f"todo.{group_name}": {}}}
    # )
    # return {group_name: {}}


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
