from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.mcp import McpSettingsRead, McpSettingsWrite, McpTokenCreated
from app.services.mcp_settings import McpSettingsError, McpSettingsService

router = APIRouter(prefix="/settings/mcp", tags=["settings"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("", response_model=McpSettingsRead)
def read_mcp_settings(session: SessionDependency) -> McpSettingsRead:
    return McpSettingsService(session).read()


@router.put("", response_model=McpSettingsRead)
def update_mcp_settings(
    payload: McpSettingsWrite,
    session: SessionDependency,
) -> McpSettingsRead:
    try:
        return McpSettingsService(session).update(payload)
    except McpSettingsError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/token", response_model=McpTokenCreated, status_code=status.HTTP_201_CREATED)
def rotate_mcp_token(session: SessionDependency) -> McpTokenCreated:
    return McpSettingsService(session).rotate_token()
