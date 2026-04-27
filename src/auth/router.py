import uuid

from fastapi import APIRouter
from fastapi_users import FastAPIUsers
from auth.backend.backend import auth_backend
from auth.dependencies.user_manager import get_user_manager

from auth.models.user import User
from auth.schemas import UserRead, UserCreate
from .config import AuthConfig

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

router = APIRouter(
    prefix=AuthConfig.api_prefix,
    tags=[AuthConfig.api_tag],
)

router.include_router(fastapi_users.get_auth_router(auth_backend))

router.include_router(fastapi_users.get_register_router(UserRead, UserCreate))

router.include_router(fastapi_users.get_verify_router(UserRead))

router.include_router(fastapi_users.get_reset_password_router())


current_active_verified_user = fastapi_users.current_user(
    active=True,
    verified=True,
)
