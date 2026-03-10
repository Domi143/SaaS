from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.tokens import decode_token
from app.core.config import settings
from app.db.session import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenPair
from app.services.auth_service import AuthService


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register_user_endpoint(
    payload: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    service = AuthService(db)
    try:
        user = await service.register_user(email=payload.email, password=payload.password)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User exists") from None

    access, refresh = service.create_token_pair(user.id)
    _set_auth_cookies(response, access, refresh)
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenPair)
async def login_endpoint(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    service = AuthService(db)
    user = await service.authenticate_user(email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")

    access, refresh = service.create_token_pair(user.id)
    _set_auth_cookies(response, access, refresh)
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenPair)
async def refresh_endpoint(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
) -> TokenPair:
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    try:
        payload = decode_token(refresh_token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED) from None
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    # In diesem MVP nutzen wir das Refresh‑Token nur zum Erzeugen eines neuen Access‑Tokens.
    from app.auth.tokens import create_access_token

    new_access = create_access_token(str(user_id))
    _set_single_access_cookie(response, new_access)
    return TokenPair(access_token=new_access, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_endpoint(response: Response) -> None:
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


def _set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    cookie_params = {
        "httponly": True,
        "secure": settings.app_env == "production",
        "samesite": "strict",
        "path": "/",
    }
    response.set_cookie("access_token", access, **cookie_params)
    response.set_cookie("refresh_token", refresh, **cookie_params)


def _set_single_access_cookie(response: Response, access: str) -> None:
    cookie_params = {
        "httponly": True,
        "secure": settings.app_env == "production",
        "samesite": "strict",
        "path": "/",
    }
    response.set_cookie("access_token", access, **cookie_params)

