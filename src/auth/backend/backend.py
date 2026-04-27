from fastapi_users.authentication import AuthenticationBackend

from auth.config import AuthConfig
from auth.dependencies.strategy import get_session_strategy
from .transport import cookie_transport

auth_backend = AuthenticationBackend(
    name=AuthConfig.backend_name,
    transport=cookie_transport,
    get_strategy=get_session_strategy,
)
