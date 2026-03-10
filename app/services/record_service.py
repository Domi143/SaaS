from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Record, RecordValue, WorkspaceField
from app.repositories.records import RecordRepository, RecordValueRepository
from app.repositories.workspaces import WorkspaceFieldRepository, WorkspaceRepository
from app.services.plan_service import PlanService


class RecordService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.workspaces = WorkspaceRepository(db)
        self.fields = WorkspaceFieldRepository(db)
        self.records = RecordRepository(db)
        self.values = RecordValueRepository(db)
        self.plans = PlanService(db)

    async def create_record(self, user_id: int, workspace_id: int, values_by_field: dict[int, str]) -> int:
        ws = await self.workspaces.get_for_user(user_id, workspace_id)
        if not ws:
            raise LookupError("Workspace not found")
        plan_name = await self.plans.get_user_plan_name(user_id)
        await self.plans.ensure_can_create_record(workspace_id, plan_name)

        rec = await self.records.create(workspace_id=workspace_id)
        for field_id, value in values_by_field.items():
            await self.values.upsert_text(rec.id, field_id, value)
        await self.db.commit()
        return rec.id

    async def update_record(self, user_id: int, workspace_id: int, record_id: int, values_by_field: dict[int, str]) -> None:
        ws = await self.workspaces.get_for_user(user_id, workspace_id)
        if not ws:
            raise LookupError("Workspace not found")
        rec = await self.records.get_in_workspace(workspace_id, record_id)
        if not rec:
            raise LookupError("Record not found")
        for field_id, value in values_by_field.items():
            await self.values.upsert_text(rec.id, field_id, value)
        await self.db.commit()

    async def delete_record(self, user_id: int, workspace_id: int, record_id: int) -> None:
        ws = await self.workspaces.get_for_user(user_id, workspace_id)
        if not ws:
            raise LookupError("Workspace not found")
        ok = await self.records.delete_in_workspace(workspace_id, record_id)
        if not ok:
            raise LookupError("Record not found")
        await self.db.commit()

    async def list_records_matrix(
        self,
        user_id: int,
        workspace_id: int,
        search: str | None = None,
        sort: str | None = None,
        direction: str = "asc",
    ) -> tuple[list[WorkspaceField], list[dict[str, str]]]:
        ws = await self.workspaces.get_for_user(user_id, workspace_id)
        if not ws:
            raise LookupError("Workspace not found")

        fields = await self.fields.list_for_workspace(workspace_id)
        field_ids = [f.id for f in fields]

        recs_q = select(Record).where(Record.workspace_id == workspace_id).order_by(Record.id.desc())
        recs = list((await self.db.execute(recs_q)).scalars().all())

        values_q = select(RecordValue).where(RecordValue.record_id.in_([r.id for r in recs])) if recs else None
        values: list[RecordValue] = []
        if values_q is not None:
            values = list((await self.db.execute(values_q)).scalars().all())

        by_record: dict[int, dict[int, RecordValue]] = {}
        for rv in values:
            by_record.setdefault(rv.record_id, {})[rv.field_id] = rv

        rows: list[dict[str, str]] = []
        for r in recs:
            row: dict[str, str] = {"_id": str(r.id)}
            for f in fields:
                rv = by_record.get(r.id, {}).get(f.id)
                val = ""
                if rv and rv.value_text is not None:
                    val = rv.value_text
                row[str(f.id)] = val
            rows.append(row)

        if search:
            needle = search.strip().lower()
            if needle:
                rows = [row for row in rows if any(needle in (v or "").lower() for k, v in row.items() if k != "_id")]

        # sort by one field id string
        if sort and sort in {str(fid) for fid in field_ids}:
            rows.sort(key=lambda r: (r.get(sort) or "").lower(), reverse=(direction == "desc"))

        return fields, rows

