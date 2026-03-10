from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plans import PLAN_FREE, get_plan_limits
from app.models import BillingCustomer, Record, Workspace


class PlanService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user_plan_name(self, user_id: int) -> str:
        result = await self.db.execute(
            select(BillingCustomer.plan_name).where(BillingCustomer.user_id == user_id)
        )
        plan = result.scalar_one_or_none()
        return plan or PLAN_FREE

    async def ensure_can_create_workspace(self, user_id: int) -> None:
        plan_name = await self.get_user_plan_name(user_id)
        limits = get_plan_limits(plan_name)
        result = await self.db.execute(
            select(func.count(Workspace.id)).where(Workspace.user_id == user_id)
        )
        count = int(result.scalar_one())
        if count >= limits.max_workspaces:
            raise PermissionError("Workspace limit reached")

    async def ensure_can_create_record(self, workspace_id: int, user_plan_name: str) -> None:
        limits = get_plan_limits(user_plan_name)
        result = await self.db.execute(
            select(func.count(Record.id)).where(Record.workspace_id == workspace_id)
        )
        count = int(result.scalar_one())
        if count >= limits.max_records:
            raise PermissionError("Record limit reached")

