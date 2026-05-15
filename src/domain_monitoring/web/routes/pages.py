from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="web/templates")

router = APIRouter(prefix="/web", include_in_schema=False)


def _auth_context(
    active_form: str,
    values: dict | None = None,
    errors: dict | None = None,
) -> dict:
    return {
        "active_form": active_form,
        "values": values or {},
        "errors": errors or {},
    }


@router.get("/login", response_class=HTMLResponse)
async def get_login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "auth/entry/auth.html",
        _auth_context("login"),
    )


@router.get("/register", response_class=HTMLResponse)
async def get_register_page(request: Request):
    return templates.TemplateResponse(
        request,
        "auth/entry/auth.html",
        _auth_context("register"),
    )
