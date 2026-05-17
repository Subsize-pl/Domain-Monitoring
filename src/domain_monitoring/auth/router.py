from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError

from domain_monitoring.auth.backend.backend import auth_backend
from domain_monitoring.auth.backend.transport import cookie_transport
from domain_monitoring.auth.config import AuthConfig
from domain_monitoring.auth.dependencies.current_user import (
    get_current_active_user,
)
from domain_monitoring.auth.fastapi_users import fastapi_users
from domain_monitoring.auth.dependencies.user_manager import get_user_manager
from domain_monitoring.auth.schemas import (
    LoginForm,
    RegisterForm,
    UserCreate,
    UserRead,
)
from domain_monitoring.core.utils.pydantic_errors_mapping import map_validation_errors
from domain_monitoring.web.routes.auth import render_auth_page
from domain_monitoring.core.config.settings import get_settings
from domain_monitoring.core.utils.log.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(
    prefix=AuthConfig.api_prefix,
    tags=[AuthConfig.api_tag],
)

router.include_router(fastapi_users.get_verify_router(UserRead))
router.include_router(fastapi_users.get_reset_password_router())


@router.post(
    "/login",
    response_class=HTMLResponse,
)
async def login(
    request: Request,
    username: Annotated[str | None, Form()] = None,
    password: Annotated[str | None, Form()] = None,
    user_manager=Depends(get_user_manager),
    strategy=Depends(auth_backend.get_strategy),
):
    values = {"login_username": username or ""}

    try:
        payload = LoginForm(username=username, password=password)
    except ValidationError as exc:
        return render_auth_page(
            request,
            active_form="login",
            values=values,
            errors=map_validation_errors(exc, prefix="login"),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    logger.info("[LOGIN] Attempt username='%s'", payload.username)

    user = await user_manager.authenticate(
        OAuth2PasswordRequestForm(
            username=payload.username,
            password=payload.password,
        )
    )

    if user is None:
        return render_auth_page(
            request,
            active_form="login",
            values=values,
            errors={
                "login_username": "Invalid credentials.",
                "login_password": "Invalid credentials.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    response = await auth_backend.login(strategy, user)

    response.status_code = status.HTTP_303_SEE_OTHER
    response.headers["Location"] = settings.urls.USER_ROOT_DASHBOARD_PAGE
    return response


@router.post(
    "/register",
    response_class=HTMLResponse,
)
async def register(
    request: Request,
    username: Annotated[str | None, Form()] = None,
    email: Annotated[str | None, Form()] = None,
    password: Annotated[str | None, Form()] = None,
    confirm_password: Annotated[str | None, Form()] = None,
    user_manager=Depends(get_user_manager),
    strategy=Depends(auth_backend.get_strategy),
):
    values = {
        "register_username": username or "",
        "register_email": email or "",
    }

    try:
        payload = RegisterForm(
            username=username,
            email=email,
            password=password,
            confirm_password=confirm_password,
        )
    except ValidationError as exc:
        return render_auth_page(
            request,
            active_form="register",
            values=values,
            errors=map_validation_errors(exc, prefix="register"),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if await user_manager.user_db.get_by_username(payload.username) is not None:
        return render_auth_page(
            request,
            active_form="register",
            values=values,
            errors={"register_username": "A user with this username already exists."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if await user_manager.get_by_email(payload.email) is not None:
        return render_auth_page(
            request,
            active_form="register",
            values=values,
            errors={"register_email": "A user with this email already exists."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user = await user_manager.create(
        UserCreate(
            username=payload.username,
            email=payload.email,
            password=payload.password,
        )
    )

    response = await auth_backend.login(strategy, user)

    response.status_code = status.HTTP_303_SEE_OTHER
    response.headers["Location"] = "/dashboard"
    return response


@router.post(
    "/logout",
)
async def logout(
    request: Request,
    user=Depends(get_current_active_user),
    strategy=Depends(auth_backend.get_strategy),
):
    logger.info("[LOGOUT] Attempt user_id=%s", user.id)

    token = request.cookies.get(cookie_transport.cookie_name)
    if not token:
        logger.warning("[LOGOUT] Missing token for user_id=%s", user.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )

    response = await auth_backend.logout(strategy, user, token)

    logger.info("[LOGOUT] Success user_id=%s", user.id)

    response.status_code = status.HTTP_303_SEE_OTHER
    response.headers["Location"] = "/login"
    return response
