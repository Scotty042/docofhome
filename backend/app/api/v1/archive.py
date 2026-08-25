from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.asset_engine import AssetRead
from app.services.archive import ArchivedAssetService
from app.services.asset_engine import ResourceNotFoundError

router = APIRouter(prefix="/archive", tags=["archive"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("/assets/{record_id}", response_model=AssetRead)
def get_archived_asset(record_id: UUID, session: SessionDependency) -> AssetRead:
    """Return one archived Asset as immutable historical data."""

    try:
        return ArchivedAssetService(session).get_read(record_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Archived Asset not found") from exc
