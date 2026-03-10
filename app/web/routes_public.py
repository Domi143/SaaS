from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.plans import PLAN_FREE, PLAN_PLUS, PLAN_PRO, get_plan_limits


templates = Jinja2Templates(directory="app/templates")

router = APIRouter(tags=["public"])


@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request) -> HTMLResponse:
    plans = [
        get_plan_limits(PLAN_FREE),
        get_plan_limits(PLAN_PLUS),
        get_plan_limits(PLAN_PRO),
    ]
    return templates.TemplateResponse(
        "public/landing.html",
        {
            "request": request,
            "plans": plans,
        },
    )

