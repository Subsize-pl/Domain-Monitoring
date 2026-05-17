from domain_monitoring.auth.fastapi_users import fastapi_users

get_current_active_user = fastapi_users.current_user(active=True)
get_current_active_verified_user = fastapi_users.current_user(
    active=True,
    verified=True,
)
