from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.immich import (
    ImmichAlbumListRead,
    ImmichImagePageRead,
    ImmichLinkListRead,
    ImmichLinkRead,
    ImmichLinkWrite,
)
from app.services.immich import (
    ImmichConfigurationError,
    ImmichFilterConflictError,
    ImmichImageNotFoundError,
    ImmichLinkConflictError,
    ImmichLinkNotFoundError,
    ImmichService,
    ImmichUnavailableError,
)

router = APIRouter(prefix="/immich", tags=["immich"])
SessionDependency = Annotated[Session, Depends(get_session)]


def _translate_error(exc: RuntimeError) -> HTTPException:
    if isinstance(
        exc,
        ImmichConfigurationError | ImmichLinkConflictError | ImmichFilterConflictError,
    ):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, ImmichImageNotFoundError | ImmichLinkNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=502, detail=str(exc))


@router.get("/assets", response_model=ImmichImagePageRead)
def browse_images(
    session: SessionDependency,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=24, ge=1, le=100),
    search: str | None = Query(default=None, max_length=255),
    album_id: UUID | None = None,
    favorite_only: bool = Query(default=False),
    taken_after: datetime | None = None,
    taken_before: datetime | None = None,
) -> ImmichImagePageRead:
    try:
        return ImmichService(session).browse_images(
            page=page,
            page_size=page_size,
            search=search,
            album_id=album_id,
            favorite_only=favorite_only,
            taken_after=taken_after,
            taken_before=taken_before,
        )
    except (
        ImmichConfigurationError,
        ImmichFilterConflictError,
        ImmichUnavailableError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.get("/albums", response_model=ImmichAlbumListRead)
def list_albums(session: SessionDependency) -> ImmichAlbumListRead:
    try:
        return ImmichService(session).list_albums()
    except (ImmichConfigurationError, ImmichUnavailableError) as exc:
        raise _translate_error(exc) from exc


@router.get("/assets/{immich_asset_id}/thumbnail")
def thumbnail(immich_asset_id: UUID, session: SessionDependency) -> Response:
    try:
        image = ImmichService(session).thumbnail(immich_asset_id)
    except (
        ImmichConfigurationError,
        ImmichImageNotFoundError,
        ImmichUnavailableError,
    ) as exc:
        raise _translate_error(exc) from exc
    return Response(
        content=image.content,
        media_type=image.media_type,
        headers={"Cache-Control": "private, max-age=300"},
    )


@router.get("/links", response_model=ImmichLinkListRead)
def list_links(asset_id: UUID, session: SessionDependency) -> ImmichLinkListRead:
    try:
        return ImmichService(session).list_links(asset_id=asset_id)
    except ImmichLinkNotFoundError as exc:
        raise _translate_error(exc) from exc


@router.post("/links", response_model=ImmichLinkRead, status_code=status.HTTP_201_CREATED)
def create_link(payload: ImmichLinkWrite, session: SessionDependency) -> ImmichLinkRead:
    try:
        return ImmichService(session).create_link(payload)
    except (
        ImmichConfigurationError,
        ImmichImageNotFoundError,
        ImmichLinkConflictError,
        ImmichLinkNotFoundError,
        ImmichUnavailableError,
    ) as exc:
        raise _translate_error(exc) from exc


@router.delete("/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(link_id: UUID, session: SessionDependency) -> Response:
    try:
        ImmichService(session).delete_link(link_id)
    except ImmichLinkNotFoundError as exc:
        raise _translate_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
