from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plans import PLAN_FREE, PLAN_PLUS, PLAN_PRO, get_plan_limits
from app.models import BillingCustomer, WebhookEvent
from app.repositories.billing import BillingRepository


class BillingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = BillingRepository(db)

    async def get_or_create_profile(self, user_id: int) -> BillingCustomer:
        profile = await self.repo.get_for_user(user_id)
        if profile:
            return profile
        limits = get_plan_limits(PLAN_FREE)
        profile = BillingCustomer(
            user_id=user_id,
            plan_name=limits.name,
            subscription_status="inactive",
            storage_limit_bytes=limits.storage_limit_bytes,
        )
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def mark_webhook_processed(self, provider: str, event_id: str) -> bool:
        ev = WebhookEvent(provider=provider, event_id=event_id)
        self.db.add(ev)
        try:
            await self.db.commit()
            return True
        except IntegrityError:
            await self.db.rollback()
            return False

    async def apply_subscription_update(
        self,
        user_id: int | None,
        paddle_customer_id: str | None,
        paddle_subscription_id: str | None,
        status: str,
        plan_name: str,
        current_period_end: datetime | None,
    ) -> None:
        if user_id is None and paddle_subscription_id:
            existing = await self.repo.get_by_subscription_id(paddle_subscription_id)
            if existing:
                user_id = existing.user_id

        if user_id is None:
            raise LookupError("Unable to map event to user")

        profile = await self.get_or_create_profile(user_id)
        profile.paddle_customer_id = paddle_customer_id or profile.paddle_customer_id
        profile.paddle_subscription_id = paddle_subscription_id or profile.paddle_subscription_id
        profile.subscription_status = status
        profile.plan_name = plan_name
        profile.current_period_end = current_period_end
        profile.storage_limit_bytes = get_plan_limits(plan_name).storage_limit_bytes
        await self.db.commit()

