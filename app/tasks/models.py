from typing import Annotated
from typing import Any
from typing import List

from bson import ObjectId
from pydantic import BaseModel, Field
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema

class ObjectIdPydanticAnnotation:
    """Определяет обертку вокруг класса ObjectID из mongodb, добавляя сериализацию."""

    @classmethod
    def validate_object_id(cls, v: Any, handler) -> ObjectId:
        """Валидирует ObjectId.

        Args:
            v (Any): Значение для валидации.
            handler: Обработчик для преобразования значения.

        Returns:
            ObjectId: Валидированный ObjectId.

        Raises:
            ValueError: Если ObjectId невалиден.
        """
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
        """Получает схему валидации для Pydantic.

        Args:
            source_type: Тип источника.
            _handler: Обработчик для преобразования значения.

        Returns:
            core_schema.CoreSchema: Схема валидации.
        """
        assert source_type is ObjectId  # noqa: S101
        return core_schema.no_info_wrap_validator_function(
            cls.validate_object_id,
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema, handler) -> JsonSchemaValue:
        """Получает JSON схему для Pydantic.

        Args:
            _core_schema: Схема валидации.
            handler: Обработчик для преобразования значения.

        Returns:
            JsonSchemaValue: JSON схема.
        """
        return handler(core_schema.str_schema())

class Task(BaseModel):
    """Модель задачи, представляющая задачу в системе."""
    id: Annotated[ObjectId, ObjectIdPydanticAnnotation] | None = Field(
        default=None,
        alias="_id",
    )
    title: str
    description: str
    order_num: int

class GetTaskGroup(BaseModel):
    """Модель группы задач, представляющая группу задач в системе."""
    id: Annotated[ObjectId, ObjectIdPydanticAnnotation] | None = Field(
        default=None,
        alias="_id",
    )
    title: str
    order_num: int
    tasks: List[Task]

class TaskGroupCreate(BaseModel):
    """Модель для создания группы задач."""
    title: str

class TaskCreate(BaseModel):
    """Модель для создания задачи."""
    description: str = ""
