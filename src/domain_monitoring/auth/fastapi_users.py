import uuid

from fastapi_users import FastAPIUsers

from domain_monitoring.auth.backend import auth_backend
from domain_monitoring.auth.dependencies.user_manager import get_user_manager
from domain_monitoring.auth.models import User

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)
