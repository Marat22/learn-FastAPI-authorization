from typing import Any, Dict

from bson import ObjectId
from fastapi.exceptions import HTTPException

from app.database import users

from pymongo.results import UpdateResult


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


def get_task(task_group: dict[str, Any], task_name: str) -> dict[str, Any]:
    return next(
        (t for t in task_group["tasks"] if t["title"] == task_name), None
    )


def get_task_group(user, group_name):
    return next(
        (g for g in user["todo"] if g["title"] == group_name),
        None
    )


# async def update_task_group(user: dict[str, Any], group_id, group_data):
#     update_data = {
#         f"todo.task_groups.$.{k}": v
#         for k, v in group_data.dict(exclude_unset=True).items()
#     }
#     update_data["todo.task_groups.$.updated_at"] = datetime.now()
#
#     result = await users.update_one(
#         {"_id": user["_id"], "todo.task_groups._id": group_id},
#         {"$set": update_data}
#     )
#     if result.modified_count == 0:
#         return None
#     return await get_task_group(user, group_id)


async def delete_task_group(user: dict[str, Any], group_name: str) -> Dict[str, str]:
    """
    Deletes a task group by name and updates order numbers for remaining groups.
    Returns success message or raises appropriate HTTPException.
    """
    try:
        # 1. Find the group to get its order number
        user_doc = await users.find_one(
            {"_id": user["_id"], "todo.title": group_name},
            {"todo.$": 1}
        )

        if not user_doc or not user_doc.get("todo"):
            raise HTTPException(status_code=404, detail="Group not found")

        deleted_order = user_doc["todo"][0]["order_num"]

        # 2. Remove the group
        delete_result = await users.update_one(
            {"_id": user["_id"]},
            {"$pull": {"todo": {"title": group_name}}}
        )

        if delete_result.modified_count != 1:
            raise HTTPException(status_code=404, detail="Group not found or already deleted")

        # 3. Update order numbers for groups with higher order
        update_result = await users.update_one(
            {"_id": user["_id"]},
            [{
                "$set": {
                    "todo": {
                        "$map": {
                            "input": "$todo",
                            "as": "group",
                            "in": {
                                "$mergeObjects": [
                                    "$$group",
                                    {
                                        "order_num": {
                                            "$cond": {
                                                "if": {"$gt": ["$$group.order_num", deleted_order]},
                                                "then": {"$subtract": ["$$group.order_num", 1]},
                                                "else": "$$group.order_num"
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            }]
        )

        if update_result.modified_count == 1:
            return {"Result": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to create task group")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database operation failed: {str(e)}")


async def rename_task_group(user: dict[str, Any], old_group_name: str, new_group_name: str) -> Dict[str, str]:
    """
    Renames a task group atomically while ensuring:
    - Old group exists
    - New name isn't taken
    - Proper error handling
    """
    # Validate input
    if not old_group_name or not new_group_name:
        raise HTTPException(status_code=400, detail="Group names cannot be empty")
    if old_group_name == new_group_name:
        raise HTTPException(status_code=400, detail="New name must be different from old name")

    try:
        # Atomic update operation
        result = await users.update_one(
            {
                "_id": user["_id"],
                "$and": [
                    {"todo.title": old_group_name},
                    {"todo.title": {"$ne": new_group_name}}
                ]
            },
            {"$set": {"todo.$[elem].title": new_group_name}},
            array_filters=[{"elem.title": old_group_name}]
        )

        # Handle update results
        if result.modified_count == 1:
            return {"Result": "success"}

        # Determine why update failed
        group_exists = await users.find_one({
            "_id": user["_id"],
            "todo.title": new_group_name
        })

        if group_exists:
            raise HTTPException(status_code=409,
                                detail=f"Group '{new_group_name}' already exists")
        else:
            raise HTTPException(status_code=404,
                                detail=f"Group '{old_group_name}' not found")

    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Database error: {str(e)}")


async def create_task(user: dict[str, Any], group_name: str, task_name: str, description: str) -> Dict[str, str]:
    if not task_name or not isinstance(task_name, str):
        raise HTTPException(status_code=400, detail="Task name must be a non-empty string")

    group = get_task_group(user, group_name)
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check if task already exists
    if get_task(group, task_name) is not None:
        raise HTTPException(status_code=409, detail=f"Task group '{group_name}' already exists")

    new_task_id = ObjectId()

    new_order_num = max(t["order_num"] for t in group["tasks"]) + 1 if group["tasks"] else 1

    result: UpdateResult = await users.update_one(
        {"_id": user["_id"], "todo.title": group_name},
        {
            "$push": {
                "todo.$.tasks": {
                    "_id": new_task_id,
                    "title": group_name,
                    "description": description,
                    "order_num": new_order_num,
                }
            }
        }
    )

    # Check if the update was successful
    if result.modified_count == 1:
        return {"Result": "success", "task_id": str(new_task_id)}
    else:
        raise HTTPException(status_code=500, detail="Failed to create task")

# async def get_task(user, group_id, task_id):
#     group = await get_task_group(user, group_id)
#     if not group:
#         return None
#     return next((t for t in group["tasks"] if t["_id"] == task_id), None)
#
#
# async def update_task(user, group_id, task_id, task_data):
#     update_data = {
#         f"todo.task_groups.$[group].tasks.$[task].{k}": v
#         for k, v in task_data.dict(exclude_unset=True).items()
#     }
#     update_data["todo.task_groups.$[group].tasks.$[task].updated_at"] = datetime.now()
#
#     result = await users.update_one(
#         {"_id": user["_id"], "todo.task_groups._id": group_id},
#         {"$set": update_data},
#         array_filters=[
#             {"group._id": group_id},
#             {"task._id": task_id}
#         ]
#     )
#     return result.modified_count > 0
#
#
# async def delete_task(user, group_id, task_id):
#     result = await users.update_one(
#         {"_id": user["_id"], "todo.task_groups._id": group_id},
#         {"$pull": {"todo.task_groups.$.tasks": {"_id": task_id}}}
#     )
#     return result.modified_count > 0
