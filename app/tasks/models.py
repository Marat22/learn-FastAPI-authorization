# app/tasks/models.py
from datetime import datetime
from typing import Optional, List

from bson import ObjectId
from pydantic import BaseModel, Field


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "pending"


class TaskCreate(TaskBase):
    pass


class TaskUpdate(TaskBase):
    pass


class TaskOut(TaskBase):
    task_id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True


class TaskGroupBase(BaseModel):
    title: str
    description: Optional[str] = None


class TaskGroupCreate(TaskGroupBase):
    pass


class TaskGroupUpdate(TaskGroupBase):
    pass


class TaskGroupOut(TaskGroupBase):
    group_name: str
    tasks: List[TaskOut]
