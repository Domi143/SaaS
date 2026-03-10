from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import routes_auth as api_auth, routes_billing as api_billing, routes_workspaces as api_workspaces
from app.core.config import settings
from app.core.csrf import CSRF_COOKIE_NAME, new_csrf_token, verify_csrf
from app.web import (
    routes_app,
    routes_auth as web_auth,
    routes_billing as web_billing,
    routes_public,
    routes_workspaces,
)
from app.web.error_handlers import not_found, server_error


def create_app() -> FastAPI:
    app = FastAPI(title="FlexDB", debug=settings.debug)

    @app.middleware("http")
    async def csrf_middleware(request: Request, call_next):
        if CSRF_COOKIE_NAME in request.cookies:
            request.state.csrf_token = request.cookies.get(CSRF_COOKIE_NAME)
        else:
            request.state.csrf_token = new_csrf_token()

        # Skip CSRF for safe methods and API/webhook endpoints
        if request.method in ("GET", "HEAD", "OPTIONS"):
            response = await call_next(request)
        else:
            if request.url.path.startswith("/api/") or request.url.path.startswith("/billing/webhook"):
                response = await call_next(request)
            else:
                await verify_csrf(request)
                response = await call_next(request)

        # Ensure CSRF cookie exists for browser pages
        if CSRF_COOKIE_NAME not in request.cookies:
            response.set_cookie(
                CSRF_COOKIE_NAME,
                request.state.csrf_token,
                httponly=False,
                secure=settings.app_env == "production",
                samesite="strict",
                path="/",
            )
        return response

    if settings.backend_cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(o) for o in settings.backend_cors_origins],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    app.include_router(routes_public.router)
    app.include_router(web_auth.router)
    app.include_router(routes_app.router)
    app.include_router(routes_workspaces.router)
    app.include_router(web_billing.router)

    app.include_router(api_auth.router)
    app.include_router(api_billing.router)
    app.include_router(api_workspaces.router)

    app.add_exception_handler(StarletteHTTPException, not_found)
    app.add_exception_handler(Exception, server_error)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

