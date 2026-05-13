from datetime import datetime, timezone

from fastapi import status
from fastapi.requests import Request

from domain_monitoring.web.routes.pages import templates


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def render_auth_page(
    request: Request,
    *,
    active_form: str,
    values: dict | None = None,
    errors: dict | None = None,
    status_code: int = status.HTTP_200_OK,
):
    # TODO: take out hardcoded url to core config file
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
