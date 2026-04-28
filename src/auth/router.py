import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import FastAPIUsers
from pydantic import ValidationError

from auth.backend.backend import auth_backend
from auth.backend.transport import cookie_transport
from auth.config import AuthConfig
from auth.dependencies.security import same_origin_dependency
from auth.dependencies.user_manager import get_user_manager
from auth.models.user import User
from auth.schemas import LoginForm, RegisterForm, UserCreate, UserRead
from core.utils.log.logger import get_logger
from web.routes.pages import templates

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

router = APIRouter(
    prefix=AuthConfig.api_prefix,
    tags=[AuthConfig.api_tag],
)

router.include_router(fastapi_users.get_verify_router(UserRead))
router.include_router(fastapi_users.get_reset_password_router())

current_active_user = fastapi_users.current_user(active=True)
current_active_verified_user = fastapi_users.current_user(active=True, verified=True)

logger = get_logger(__name__)


def _render_auth_page(
    request: Request,
    *,
    active_form: str,
    values: dict | None = None,
    errors: dict | None = None,
    status_code: int = status.HTTP_200_OK,
):
    return templates.TemplateResponse(
        request,
        "auth/entry/auth.html",
        {
            "request": request,
            "active_form": active_form,
            "values": values or {},
            "errors": errors or {},
        },
        status_code=status_code,
    )


def _map_validation_errors(exc: ValidationError, *, prefix: str) -> dict[str, str]:
    mapped: dict[str, str] = {}

    for error in exc.errors():
        loc = error.get("loc", ())
        key = str(loc[-1]) if loc else "form"

        if key in {"__root__", "form"}:
            mapped[f"{prefix}_form"] = error["msg"]
            continue

        mapped[f"{prefix}_{key}"] = error["msg"]

    return mapped


@router.post(
    "/login",
    response_class=HTMLResponse,
    dependencies=[Depends(same_origin_dependency)],
)
async def login(
    request: Request,
    username: Annotated[str | None, Form()] = None,
    password: Annotated[str | None, Form()] = None,
    user_manager=Depends(get_user_manager),
    strategy=Depends(auth_backend.get_strategy),
):
    values = {
        "login_username": username or "",
    }

    errors: dict[str, str] = {}

    if not username or not username.strip():
        errors["login_username"] = "Username is required."

    if not password:
        errors["login_password"] = "Password is required."

    if errors:
        return _render_auth_page(
            request,
            active_form="login",
            values=values,
            errors=errors,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        payload = LoginForm(username=username, password=password)
    except ValidationError as exc:
        return _render_auth_page(
            request,
            active_form="login",
            values=values,
            errors=_map_validation_errors(exc, prefix="login"),
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
        return _render_auth_page(
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
    response.headers["Location"] = "/dashboard"
    return response


@router.post(
    "/register",
    response_class=HTMLResponse,
    dependencies=[Depends(same_origin_dependency)],
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

    errors: dict[str, str] = {}

    if not username or not username.strip():
        errors["register_username"] = "Username is required."

    if not email or not email.strip():
        errors["register_email"] = "Email is required."

    if not password:
        errors["register_password"] = "Password is required."

    if not confirm_password or (password and password != confirm_password):
        errors["register_password"] = "Please confirm your password."

    if errors:
        return _render_auth_page(
            request,
            active_form="register",
            values=values,
            errors=errors,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        payload = RegisterForm(
            username=username,
            email=email,
            password=password,
            confirm_password=confirm_password,
        )
    except ValidationError as exc:
        return _render_auth_page(
            request,
            active_form="register",
            values=values,
            errors=_map_validation_errors(exc, prefix="register"),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    existing_username = await user_manager.user_db.get_by_username(payload.username)
    if existing_username is not None:
        return _render_auth_page(
            request,
            active_form="register",
            values=values,
            errors={"register_username": "A user with this username already exists."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    existing_email = await user_manager.get_by_email(payload.email)
    if existing_email is not None:
        return _render_auth_page(
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
    dependencies=[Depends(same_origin_dependency)],
)
async def logout(
    request: Request,
    user=Depends(current_active_user),
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
    response.headers["Location"] = "/web/login"
    return response
