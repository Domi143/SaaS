from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService


templates = Jinja2Templates(directory="app/templates")

router = APIRouter(tags=["auth"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("public/login.html", {"request": request})


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse | HTMLResponse:
    service = AuthService(db)
    user = await service.authenticate_user(email=email, password=password)
    if not user:
        return templates.TemplateResponse(
            "public/login.html",
            {"request": request, "error": "Ungültige Zugangsdaten"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    access, refresh = service.create_token_pair(user.id)
    from app.api.routes_auth import _set_auth_cookies

    redirect = RedirectResponse(url="/app/dashboard", status_code=status.HTTP_302_FOUND)
    _set_auth_cookies(redirect, access, refresh)
    return redirect


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("public/register.html", {"request": request})


@router.post("/register")
async def register_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse | HTMLResponse:
    service = AuthService(db)
    try:
        await service.register_user(email=email, password=password)
    except ValueError:
        return templates.TemplateResponse(
            "public/register.html",
            {"request": request, "error": "Benutzer existiert bereits"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Auto‑Login nach Registrierung
    user = await service.authenticate_user(email=email, password=password)
    if not user:
        raise HTTPException(status_code=500, detail="Registration failed")
    access, refresh = service.create_token_pair(user.id)
    from app.api.routes_auth import _set_auth_cookies

    redirect = RedirectResponse(url="/app/dashboard", status_code=status.HTTP_302_FOUND)
    _set_auth_cookies(redirect, access, refresh)
    return redirect


@router.post("/logout")
async def logout_web() -> RedirectResponse:
    redirect = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    redirect.delete_cookie("access_token")
    redirect.delete_cookie("refresh_token")
    return redirect

