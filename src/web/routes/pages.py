from fastapi.templating import Jinja2Templates
from fastapi import Request, APIRouter
from fastapi.responses import HTMLResponse

templates = Jinja2Templates(directory="web/templates")

router = APIRouter(prefix="/web", include_in_schema=False)


@router.get("/login", response_class=HTMLResponse)
async def get_login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="auth/auth.html",
    )
