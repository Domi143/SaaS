from __future__ import annotations

import csv
import io
from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, Response, status
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.db.session import get_db
from app.models import Workspace
from app.repositories.workspaces import WorkspaceRepository
from app.services.record_service import RecordService
from app.services.workspace_service import WorkspaceService


templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="/app/workspaces", tags=["workspaces"])


@router.get("", response_class=HTMLResponse)
async def workspaces_page(
    request: Request,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    repo = WorkspaceRepository(db)
    workspaces = list((await db.execute(repo.list_for_user(user.id))).scalars().all())
    return templates.TemplateResponse(
        "app/workspaces.html",
        {"request": request, "user": user, "workspaces": workspaces},
    )


@router.post("")
async def create_workspace(
    request: Request,
    user: CurrentUser,
    name: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> Response:
    service = WorkspaceService(db)
    try:
        workspace_id = await service.create_workspace(user.id, name=name)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Plan limit reached") from None
    return Response(headers={"HX-Redirect": f"/app/workspaces/{workspace_id}"})


@router.get("/{workspace_id}", response_class=HTMLResponse)
async def workspace_detail(
    request: Request,
    workspace_id: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(default=None),
    sort: str | None = Query(default=None),
    direction: str = Query(default="asc"),
) -> HTMLResponse:
    ws = await WorkspaceRepository(db).get_for_user(user.id, workspace_id)
    if not ws:
        raise HTTPException(status_code=404)

    record_service = RecordService(db)
    fields, rows = await record_service.list_records_matrix(
        user_id=user.id,
        workspace_id=workspace_id,
        search=q,
        sort=sort,
        direction=direction,
    )
    return templates.TemplateResponse(
        "app/workspace_detail.html",
        {
            "request": request,
            "user": user,
            "workspace": ws,
            "fields": fields,
            "rows": rows,
            "q": q or "",
            "sort": sort or "",
            "direction": direction,
        },
    )


@router.get("/{workspace_id}/table", response_class=HTMLResponse)
async def workspace_table_partial(
    request: Request,
    workspace_id: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(default=None),
    sort: str | None = Query(default=None),
    direction: str = Query(default="asc"),
) -> HTMLResponse:
    ws = await WorkspaceRepository(db).get_for_user(user.id, workspace_id)
    if not ws:
        raise HTTPException(status_code=404)

    record_service = RecordService(db)
    fields, rows = await record_service.list_records_matrix(
        user_id=user.id,
        workspace_id=workspace_id,
        search=q,
        sort=sort,
        direction=direction,
    )
    return templates.TemplateResponse(
        "partials/workspace_table.html",
        {
            "request": request,
            "workspace": ws,
            "fields": fields,
            "rows": rows,
            "q": q or "",
            "sort": sort or "",
            "direction": direction,
        },
    )


@router.post("/{workspace_id}/fields")
async def create_field(
    workspace_id: int,
    user: CurrentUser,
    display_name: str = Form(...),
    field_type: str = Form("text"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    service = WorkspaceService(db)
    await service.create_field(user.id, workspace_id, display_name=display_name, field_type=field_type)
    return Response(headers={"HX-Redirect": f"/app/workspaces/{workspace_id}"})


@router.post("/{workspace_id}/fields/{field_id}/rename")
async def rename_field(
    workspace_id: int,
    field_id: int,
    user: CurrentUser,
    display_name: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> Response:
    service = WorkspaceService(db)
    await service.rename_field(user.id, workspace_id, field_id, new_display_name=display_name)
    return Response(headers={"HX-Redirect": f"/app/workspaces/{workspace_id}"})


@router.post("/{workspace_id}/records")
async def create_record(
    workspace_id: int,
    user: CurrentUser,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    form = await request.form()
    values: dict[int, str] = {}
    for k, v in form.items():
        if k.startswith("field_"):
            field_id = int(k.removeprefix("field_"))
            values[field_id] = str(v)

    service = RecordService(db)
    try:
        await service.create_record(user.id, workspace_id, values)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Plan limit reached") from None
    return Response(headers={"HX-Redirect": f"/app/workspaces/{workspace_id}"})


@router.post("/{workspace_id}/records/{record_id}")
async def update_record(
    workspace_id: int,
    record_id: int,
    user: CurrentUser,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    form = await request.form()
    values: dict[int, str] = {}
    for k, v in form.items():
        if k.startswith("field_"):
            field_id = int(k.removeprefix("field_"))
            values[field_id] = str(v)
    service = RecordService(db)
    await service.update_record(user.id, workspace_id, record_id, values)
    return Response(headers={"HX-Redirect": f"/app/workspaces/{workspace_id}"})


@router.post("/{workspace_id}/records/{record_id}/delete")
async def delete_record(
    workspace_id: int,
    record_id: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Response:
    service = RecordService(db)
    await service.delete_record(user.id, workspace_id, record_id)
    return Response(headers={"HX-Redirect": f"/app/workspaces/{workspace_id}"})


@router.get("/{workspace_id}/export.csv")
async def export_csv(
    workspace_id: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(default=None),
    sort: str | None = Query(default=None),
    direction: str = Query(default="asc"),
) -> StreamingResponse:
    ws = await WorkspaceRepository(db).get_for_user(user.id, workspace_id)
    if not ws:
        raise HTTPException(status_code=404)
    fields, rows = await RecordService(db).list_records_matrix(user.id, workspace_id, search=q, sort=sort, direction=direction)

    def iter_csv() -> Any:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id"] + [f.display_name for f in fields])
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate(0)
        for row in rows:
            writer.writerow([row["_id"]] + [row.get(str(f.id), "") for f in fields])
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate(0)

    filename = f"workspace-{workspace_id}.csv"
    return StreamingResponse(
        iter_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

