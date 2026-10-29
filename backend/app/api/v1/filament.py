import hashlib
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.api.v1.lego import translated
from app.api.v1.notifications import SecretSafeRoute
from app.db.session import get_session
from app.schemas.filament import (
    CloudLogin,
    FilamentConfig,
    LabelRequest,
    SlotBinding,
    SnapshotImport,
    SpoolRead,
    SpoolWrite,
)
from app.services.filament import FilamentService
from app.services.filament_images import image_path, store_image
from app.services.filament_labels import cached_label_path, labels

router = APIRouter(prefix="/filament", tags=["filament"], route_class=SecretSafeRoute)
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/settings")
def settings(session: SessionDep) -> dict[str, Any]:
    return FilamentService(session).settings()


@router.put("/settings")
def save_settings(data: FilamentConfig, session: SessionDep) -> dict[str, Any]:
    return translated(lambda: FilamentService(session).save_config(data))


@router.post("/login")
def login(data: CloudLogin, session: SessionDep) -> dict[str, Any]:
    return translated(lambda: FilamentService(session).login(data))


@router.delete("/login", status_code=204)
def logout(session: SessionDep) -> None:
    FilamentService(session).disconnect()


@router.post("/sync")
def sync(session: SessionDep) -> dict[str, Any]:
    return translated(lambda: FilamentService(session).sync())


@router.post("/import")
def import_snapshot(data: SnapshotImport, session: SessionDep) -> dict[str, Any]:
    account = hashlib.sha256(data.account_reference.encode()).hexdigest()
    return translated(
        lambda: FilamentService(session).import_cloud(
            data.spools, account=account, complete=data.complete
        )
    )


@router.get("/slots")
def slots(session: SessionDep) -> list[dict[str, Any]]:
    return FilamentService(session).slots()


@router.post("/slots/refresh")
def refresh_slots(session: SessionDep) -> dict[str, Any]:
    return translated(lambda: FilamentService(session).refresh_mqtt())


@router.put("/slots/{slot_id}", status_code=204)
def bind(slot_id: UUID, data: SlotBinding, session: SessionDep) -> None:
    translated(lambda: FilamentService(session).bind_slot(slot_id, data.spool_id))


@router.post("/labels")
def export_labels(data: LabelRequest, session: SessionDep) -> Response:
    content, media, name = translated(lambda: labels(session, data))
    return Response(
        content, media_type=media, headers={"Content-Disposition": f'attachment; filename="{name}"'}
    )


@router.get("/labels/files/{reference}", response_class=FileResponse)
def cached_label(reference: str) -> FileResponse:
    return FileResponse(
        translated(lambda: cached_label_path(reference)),
        filename="Filament-Etiketten." + reference.rsplit(".", 1)[-1],
    )


@router.get("/spools")
def search(
    session: SessionDep,
    q: str = "",
    material: str = "",
    manufacturer: str = "",
    condition: str = "",
    reorder: bool | None = None,
    archive: str = Query("active", pattern="^(active|archived|all)$"),
    in_ams: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
) -> dict[str, Any]:
    return FilamentService(session).search(
        q,
        material=material,
        manufacturer=manufacturer,
        condition=condition,
        reorder=reorder,
        archive=archive,
        in_ams=in_ams,
        offset=offset,
        limit=limit,
    )


@router.post("/spools", response_model=SpoolRead, status_code=201)
def create(data: SpoolWrite, session: SessionDep) -> SpoolRead:
    return translated(lambda: FilamentService(session).save(data))


@router.get("/spools/{spool_id}", response_model=SpoolRead)
def get(spool_id: UUID, session: SessionDep) -> SpoolRead:
    service = FilamentService(session)
    return translated(lambda: service.read(service.get(spool_id)))


@router.put("/spools/{spool_id}", response_model=SpoolRead)
def update(spool_id: UUID, data: SpoolWrite, session: SessionDep) -> SpoolRead:
    return translated(lambda: FilamentService(session).save(data, spool_id))


@router.post("/spools/{spool_id}/archive")
def archive(spool_id: UUID, session: SessionDep, delete_cloud: bool = False) -> dict[str, Any]:
    return translated(lambda: FilamentService(session).archive(spool_id, delete_cloud=delete_cloud))


@router.post("/spools/{spool_id}/restore")
def restore(spool_id: UUID, session: SessionDep) -> dict[str, Any]:
    return translated(lambda: FilamentService(session).archive(spool_id, restore=True))


@router.post("/spools/{spool_id}/store-image", response_model=SpoolRead)
def store_picture(spool_id: UUID, session: SessionDep) -> SpoolRead:
    return translated(lambda: store_image(session, spool_id))


@router.get("/images/{reference}", response_class=FileResponse)
def image(reference: str) -> FileResponse:
    return FileResponse(translated(lambda: image_path(reference)))
