from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth.dependencies import CurrentUser


templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="/app", tags=["app"])


@router.get("/", include_in_schema=False)
async def app_root() -> RedirectResponse:
    return RedirectResponse(url="/app/dashboard")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: CurrentUser) -> HTMLResponse:
    return templates.TemplateResponse(
        "app/dashboard.html",
        {"request": request, "user": user},
    )


@router.get("/account", response_class=HTMLResponse)
async def account_page(request: Request, user: CurrentUser) -> HTMLResponse:
    return templates.TemplateResponse(
        "app/account.html",
        {"request": request, "user": user},
    )

