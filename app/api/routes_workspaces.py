from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth.dependencies import CurrentUser
from app.db.session import get_db
from app.repositories.workspaces import WorkspaceRepository
from app.schemas.workspace import WorkspaceCreate, WorkspaceOut
from app.services.workspace_service import WorkspaceService


router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceOut])
async def list_workspaces(user: CurrentUser, db: AsyncSession = Depends(get_db)) -> list[WorkspaceOut]:
    repo = WorkspaceRepository(db)
    workspaces = list((await db.execute(repo.list_for_user(user.id))).scalars().all())
    return [WorkspaceOut.model_validate(w) for w in workspaces]


@router.post("", response_model=WorkspaceOut, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)
) -> WorkspaceOut:
    service = WorkspaceService(db)
    try:
        workspace_id = await service.create_workspace(user.id, payload.name)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Plan limit reached") from None
    ws = await WorkspaceRepository(db).get_for_user(user.id, workspace_id)
    assert ws is not None
    return WorkspaceOut.model_validate(ws)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(workspace_id: int, user: CurrentUser, db: AsyncSession = Depends(get_db)) -> None:
    ok = await WorkspaceRepository(db).delete_for_user(user.id, workspace_id)
    if not ok:
        raise HTTPException(status_code=404)
    await db.commit()

