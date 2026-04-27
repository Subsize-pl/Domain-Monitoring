import uuid
from pydantic import Field
from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    username: str = Field(max_length=128)


class UserCreate(schemas.BaseUserCreate):
    username: str = Field(max_length=128)


class UserUpdate(schemas.BaseUserUpdate):
    username: str | None = Field(default=None, max_length=128)
