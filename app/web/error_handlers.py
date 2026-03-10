from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="app/templates")


async def not_found(request: Request, exc) -> HTMLResponse:  # noqa: ANN001
    status_code = getattr(exc, "status_code", 500)
    if status_code == 404:
        return templates.TemplateResponse(
            "app/errors/404.html",
            {"request": request},
            status_code=404,
        )
    # For non-404 HTTP exceptions, keep minimal output (auth pages often expect 401/403).
    return HTMLResponse(content="Error", status_code=int(status_code))


async def server_error(request: Request, exc) -> HTMLResponse:  # noqa: ANN001
    return templates.TemplateResponse(
        "app/errors/500.html",
        {"request": request},
        status_code=500,
    )

