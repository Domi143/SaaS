from __future__ import annotations

import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.workspaces import WorkspaceFieldRepository, WorkspaceRepository
from app.services.plan_service import PlanService


def slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "workspace"


class WorkspaceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.workspaces = WorkspaceRepository(db)
        self.fields = WorkspaceFieldRepository(db)
        self.plans = PlanService(db)

    async def create_workspace(self, user_id: int, name: str) -> int:
        await self.plans.ensure_can_create_workspace(user_id)
        slug = slugify(name)
        ws = await self.workspaces.create(user_id=user_id, name=name, slug=slug)
        # Default field
        await self.fields.create(
            workspace_id=ws.id,
            internal_name="name",
            display_name="Name",
            field_type="text",
            is_filterable=True,
            sort_order=0,
        )
        await self.db.commit()
        return ws.id

    async def create_field(
        self,
        user_id: int,
        workspace_id: int,
        display_name: str,
        field_type: str = "text",
    ) -> int:
        ws = await self.workspaces.get_for_user(user_id, workspace_id)
        if not ws:
            raise LookupError("Workspace not found")
        internal_name = slugify(display_name).replace("-", "_")
        fields = await self.fields.list_for_workspace(workspace_id)
        sort_order = len(fields) + 1
        field = await self.fields.create(
            workspace_id=workspace_id,
            internal_name=internal_name,
            display_name=display_name,
            field_type=field_type,
            is_filterable=True,
            sort_order=sort_order,
        )
        await self.db.commit()
        return field.id

    async def rename_field(
        self, user_id: int, workspace_id: int, field_id: int, new_display_name: str
    ) -> None:
        ws = await self.workspaces.get_for_user(user_id, workspace_id)
        if not ws:
            raise LookupError("Workspace not found")
        field = await self.fields.get_in_workspace(workspace_id, field_id)
        if not field:
            raise LookupError("Field not found")
        field.display_name = new_display_name
        await self.db.commit()

