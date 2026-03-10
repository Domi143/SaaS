from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Record, RecordValue


class RecordRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def list_for_workspace(self, workspace_id: int) -> Select[tuple[Record]]:
        return select(Record).where(Record.workspace_id == workspace_id).order_by(Record.id.desc())

    async def get_in_workspace(self, workspace_id: int, record_id: int) -> Record | None:
        result = await self.db.execute(
            select(Record).where(Record.workspace_id == workspace_id, Record.id == record_id)
        )
        return result.scalar_one_or_none()

    async def create(self, workspace_id: int) -> Record:
        rec = Record(workspace_id=workspace_id)
        self.db.add(rec)
        await self.db.flush()
        return rec

    async def delete_in_workspace(self, workspace_id: int, record_id: int) -> bool:
        rec = await self.get_in_workspace(workspace_id, record_id)
        if not rec:
            return False
        await self.db.delete(rec)
        return True


class RecordValueRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_for_record(self, record_id: int) -> list[RecordValue]:
        result = await self.db.execute(select(RecordValue).where(RecordValue.record_id == record_id))
        return list(result.scalars().all())

    async def upsert_text(self, record_id: int, field_id: int, value_text: str | None) -> RecordValue:
        result = await self.db.execute(
            select(RecordValue).where(RecordValue.record_id == record_id, RecordValue.field_id == field_id)
        )
        rv = result.scalar_one_or_none()
        if rv is None:
            rv = RecordValue(record_id=record_id, field_id=field_id, value_text=value_text)
            self.db.add(rv)
            await self.db.flush()
            return rv
        rv.value_text = value_text
        rv.value_number = None
        rv.value_date = None
        rv.value_bool = None
        await self.db.flush()
        return rv

