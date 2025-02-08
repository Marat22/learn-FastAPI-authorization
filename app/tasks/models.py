from datetime import datetime
from typing import Annotated
from typing import Any
from typing import Optional, List

from bson import ObjectId
from pydantic import BaseModel, Field
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema


class ObjectIdPydanticAnnotation:
    """Defines a wrapper class around the mongodb ObjectID class adding serialization."""

    @classmethod
    def validate_object_id(cls, v: Any, handler) -> ObjectId:
        if isinstance(v, ObjectId):
            return v

        s = handler(v)
        if ObjectId.is_valid(s):
            return ObjectId(s)
        else:
            msg = "Invalid ObjectId"
            raise ValueError(msg)

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type,
        _handler,
    ) -> core_schema.CoreSchema:
        assert source_type is ObjectId  # noqa: S101
        return core_schema.no_info_wrap_validator_function(
            cls.validate_object_id,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema, handler) -> JsonSchemaValue:
        return handler(core_schema.str_schema())


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


class GetTaskGroup(BaseModel):
    id: Annotated[ObjectId, ObjectIdPydanticAnnotation] | None = Field(
        default=None,
        alias="_id",
    )
    title: str
    order_num: int
    tasks: List[TaskOut]



class TaskGroupCreate(BaseModel):
    title: str


# class TaskGroupUpdate(TaskGroupBase):
#     pass
#
#
# class TaskGroupOut(TaskGroupBase):
#     group_name: str
#     tasks: List[TaskOut]

# Request Models
# class ReorderRequest(BaseModel):
#     first_id: PyObjectId
#     second_id: PyObjectId
#
# class GroupCreate(BaseModel):
#     title: str
#
# class TaskCreate(BaseModel):
#     title: str
#     description: Optional[str] = None
#
# # Response Models
# class TaskResponse(BaseModel):
#     id: PyObjectId = Field(alias="_id")
#     title: str
#     description: Optional[str]
#     order_num: int
#
#     class Config:
#         allow_population_by_field_name = True
#
# class GroupResponse(BaseModel):
#     id: PyObjectId = Field(alias="_id")
#     title: str
#     order_num: int
#     tasks: list[TaskResponse]
#
#     class Config:
#         allow_population_by_field_name = True
