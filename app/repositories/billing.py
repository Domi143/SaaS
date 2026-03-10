from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BillingCustomer


class BillingRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_for_user(self, user_id: int) -> BillingCustomer | None:
        result = await self.db.execute(select(BillingCustomer).where(BillingCustomer.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_by_subscription_id(self, paddle_subscription_id: str) -> BillingCustomer | None:
        result = await self.db.execute(
            select(BillingCustomer).where(BillingCustomer.paddle_subscription_id == paddle_subscription_id)
        )
        return result.scalar_one_or_none()

