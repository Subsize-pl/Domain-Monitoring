from fastapi_users.authentication import CookieTransport
from domain_monitoring.auth.config import AuthConfig

cookie_transport = CookieTransport(
    cookie_name=AuthConfig.cookie_name,
    cookie_max_age=AuthConfig.cookie_max_age,
)
