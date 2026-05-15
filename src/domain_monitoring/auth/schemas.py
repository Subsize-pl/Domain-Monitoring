import uuid
from typing import Annotated

from fastapi_users import schemas
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class UserRead(schemas.BaseUser[uuid.UUID]):
    username: Annotated[str, Field(min_length=3, max_length=128)]


class UserCreate(schemas.BaseUserCreate):
    username: Annotated[str, Field(min_length=3, max_length=128)]
    password: Annotated[str, Field(min_length=8, max_length=128)]


class UserUpdate(schemas.BaseUserUpdate):
    username: Annotated[
        str | None,
        Field(default=None, min_length=3, max_length=128),
    ]


class LoginForm(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=128)]
    password: Annotated[str, Field(min_length=1, max_length=128)]

    @field_validator("username")
    @classmethod
    def normalize_identifier(cls, value: str) -> str:
        return value.strip()


class RegisterForm(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=128)]
    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=128)]
    confirm_password: Annotated[str, Field(min_length=8, max_length=128)]

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip()

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @model_validator(mode="after")
    def passwords_must_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self
