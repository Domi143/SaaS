from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core.config import settings
from app.core.plans import get_plan_limits
from app.db.session import get_db
from app.services.billing_service import BillingService


templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="/app/billing", tags=["billing-web"])


@router.get("", response_class=HTMLResponse)
async def billing_page(
    request: Request,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    profile = await BillingService(db).get_or_create_profile(user.id)
    limits = get_plan_limits(profile.plan_name)
    return templates.TemplateResponse(
        "app/billing.html",
        {
            "request": request,
            "user": user,
            "profile": profile,
            "limits": limits,
            "paddle_env": settings.paddle_env,
            "price_free": settings.paddle_price_id_free,
            "price_plus": settings.paddle_price_id_plus,
            "price_pro": settings.paddle_price_id_pro,
        },
    )

