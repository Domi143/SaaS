from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Workspace, WorkspaceField


class WorkspaceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def list_for_user(self, user_id: int) -> Select[tuple[Workspace]]:
        return select(Workspace).where(Workspace.user_id == user_id).order_by(Workspace.created_at.desc())

    async def get_for_user(self, user_id: int, workspace_id: int) -> Workspace | None:
        result = await self.db.execute(
            select(Workspace).where(Workspace.user_id == user_id, Workspace.id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: int, name: str, slug: str) -> Workspace:
        ws = Workspace(user_id=user_id, name=name, slug=slug)
        self.db.add(ws)
        await self.db.flush()
        return ws

    async def delete_for_user(self, user_id: int, workspace_id: int) -> bool:
        ws = await self.get_for_user(user_id, workspace_id)
        if not ws:
            return False
        await self.db.delete(ws)
        return True


class WorkspaceFieldRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_for_workspace(self, workspace_id: int) -> list[WorkspaceField]:
        result = await self.db.execute(
            select(WorkspaceField)
            .where(WorkspaceField.workspace_id == workspace_id)
            .order_by(WorkspaceField.sort_order.asc(), WorkspaceField.id.asc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        workspace_id: int,
        internal_name: str,
        display_name: str,
        field_type: str,
        is_filterable: bool,
        sort_order: int,
    ) -> WorkspaceField:
        field = WorkspaceField(
            workspace_id=workspace_id,
            internal_name=internal_name,
            display_name=display_name,
            field_type=field_type,
            is_filterable=is_filterable,
            sort_order=sort_order,
        )
        self.db.add(field)
        await self.db.flush()
        return field

    async def get_in_workspace(self, workspace_id: int, field_id: int) -> WorkspaceField | None:
        result = await self.db.execute(
            select(WorkspaceField).where(
                WorkspaceField.workspace_id == workspace_id, WorkspaceField.id == field_id
            )
        )
        return result.scalar_one_or_none()

