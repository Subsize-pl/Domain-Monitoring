from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import status
from fastapi.requests import Request

from domain_monitoring.core.config.settings import PROJECT_ROOT, get_settings

templates = Jinja2Templates(directory=str(PROJECT_ROOT / "web" / "templates"))
settings = get_settings()

router = APIRouter(include_in_schema=False)


def render_auth_page(
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


@router.get(
    settings.urls.ENTRY_LOGIN_PAGE,
    response_class=HTMLResponse,
)
async def get_login_page(request: Request):
    return render_auth_page(
        request,
        active_form="login",
    )


@router.get(
    settings.urls.ENTRY_REGISTER_PAGE,
    response_class=HTMLResponse,
)
async def get_register_page(request: Request):
    return render_auth_page(
        request,
        active_form="register",
    )
