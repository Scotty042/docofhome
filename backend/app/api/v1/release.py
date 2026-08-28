import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlmodel import Session, select

from app.connectors.fritzbox import FritzBoxConnector, FritzBoxConnectorError
from app.db.session import get_session
from app.models.integration_setting import IntegrationSetting
from app.schemas.release import (
    AuditEventRead,
    DashboardSettingRead,
    DashboardSettingWrite,
    DockerConnectionTestRead,
    DockerSyncResultRead,
    DockerSyncSettingRead,
    DockerSyncSettingWrite,
    FritzBoxDeviceRead,
    GuidedSetupApplyRead,
    GuidedSetupDraftRead,
    GuidedSetupDraftWrite,
    GuidedSetupPreviewRead,
    ImportPreviewRead,
    ImportResultRead,
    NetworkPathRead,
    PortGenerationPreview,
    PortGenerationResult,
    PortGenerationWrite,
    ServiceWorkloadRead,
    ServiceWorkloadWrite,
)
from app.services.release import (
    DashboardService,
    GuidedSetupService,
    NetworkExtensionService,
    PortabilityService,
    ReleaseConflictError,
    ReleaseFeatureError,
    ReleaseNotFoundError,
    ReleaseValidationError,
    WorkloadService,
)

from app.services.network import NetworkService
from app.services.docker_sync import DockerSyncError, DockerSyncService

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]


def _http_error(exc: ReleaseFeatureError) -> HTTPException:
    if isinstance(exc, ReleaseNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ReleaseConflictError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, ReleaseValidationError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=500, detail="Release-Funktion konnte nicht verarbeitet werden")


@router.get("/dashboard/config", response_model=DashboardSettingRead)
def dashboard_config(session: SessionDependency) -> DashboardSettingRead:
    return DashboardService(session).get()


@router.put("/dashboard/config", response_model=DashboardSettingRead)
def update_dashboard_config(
    payload: DashboardSettingWrite,
    session: SessionDependency,
) -> DashboardSettingRead:
    try:
        return DashboardService(session).update(payload)
    except ReleaseFeatureError as exc:
        raise _http_error(exc) from exc


@router.post("/dashboard/config/reset", response_model=DashboardSettingRead)
def reset_dashboard_config(session: SessionDependency) -> DashboardSettingRead:
    return DashboardService(session).reset()


@router.post(
    "/network/devices/{device_id}/ports/preview",
    response_model=PortGenerationPreview,
)
def preview_switch_ports(
    device_id: UUID,
    payload: PortGenerationWrite,
    session: SessionDependency,
) -> PortGenerationPreview:
    try:
        return NetworkExtensionService(session).preview_ports(device_id, payload)
    except ReleaseFeatureError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/network/devices/{device_id}/ports/generate",
    response_model=PortGenerationResult,
)
def generate_switch_ports(
    device_id: UUID,
    payload: PortGenerationWrite,
    session: SessionDependency,
) -> PortGenerationResult:
    try:
        return NetworkExtensionService(session).generate_ports(device_id, payload)
    except ReleaseFeatureError as exc:
        raise _http_error(exc) from exc


@router.get(
    "/network/devices/{device_id}/path",
    response_model=NetworkPathRead,
)
def network_path(device_id: UUID, session: SessionDependency) -> NetworkPathRead:
    try:
        return NetworkExtensionService(session).documented_path(device_id)
    except ReleaseFeatureError as exc:
        raise _http_error(exc) from exc


@router.get("/workloads", response_model=list[ServiceWorkloadRead])
def workloads(
    session: SessionDependency,
    host_asset_id: UUID | None = None,
) -> list[ServiceWorkloadRead]:
    return WorkloadService(session).list(host_asset_id=host_asset_id)


@router.post(
    "/workloads",
    response_model=ServiceWorkloadRead,
    status_code=status.HTTP_201_CREATED,
)
def create_workload(
    payload: ServiceWorkloadWrite,
    session: SessionDependency,
) -> ServiceWorkloadRead:
    try:
        return WorkloadService(session).create(payload)
    except ReleaseFeatureError as exc:
        raise _http_error(exc) from exc


@router.put("/workloads/{workload_id}", response_model=ServiceWorkloadRead)
def update_workload(
    workload_id: UUID,
    payload: ServiceWorkloadWrite,
    session: SessionDependency,
) -> ServiceWorkloadRead:
    try:
        return WorkloadService(session).update(workload_id, payload)
    except ReleaseFeatureError as exc:
        raise _http_error(exc) from exc


@router.delete("/workloads/{workload_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_workload(workload_id: UUID, session: SessionDependency) -> Response:
    try:
        WorkloadService(session).archive(workload_id)
    except ReleaseFeatureError as exc:
        raise _http_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/workloads/docker/settings", response_model=DockerSyncSettingRead)
def docker_sync_settings(session: SessionDependency) -> DockerSyncSettingRead:
    return DockerSyncService(session).get_settings()


@router.put("/workloads/docker/settings", response_model=DockerSyncSettingRead)
def update_docker_sync_settings(
    payload: DockerSyncSettingWrite,
    session: SessionDependency,
) -> DockerSyncSettingRead:
    try:
        return DockerSyncService(session).update_settings(payload)
    except DockerSyncError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/workloads/docker/test", response_model=DockerConnectionTestRead)
def test_docker_connection(session: SessionDependency) -> DockerConnectionTestRead:
    return DockerSyncService(session).test_connection()


@router.post("/workloads/docker/sync", response_model=DockerSyncResultRead)
def sync_docker_containers(session: SessionDependency) -> DockerSyncResultRead:
    try:
        return DockerSyncService(session).sync()
    except DockerSyncError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/portability/export")
def export_all(session: SessionDependency) -> Response:
    payload = PortabilityService(session).export_payload()
    return Response(
        content=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="DocOfHome-export.json"'},
    )


@router.get("/portability/export/{module}.csv")
def export_csv(module: str, session: SessionDependency) -> Response:
    try:
        content = PortabilityService(session).csv_export(module)
    except ReleaseFeatureError as exc:
        raise _http_error(exc) from exc
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="DocOfHome-{module}.csv"'},
    )


async def _import_content(file: UploadFile) -> bytes:
    return await file.read(100 * 1024 * 1024 + 1)


@router.post("/portability/import/preview", response_model=ImportPreviewRead)
async def import_preview(
    session: SessionDependency,
    file: Annotated[UploadFile, File()],
) -> ImportPreviewRead:
    try:
        return PortabilityService(session).preview(await _import_content(file))
    except ReleaseFeatureError as exc:
        raise _http_error(exc) from exc


@router.post("/portability/import", response_model=ImportResultRead)
async def import_apply(
    session: SessionDependency,
    file: Annotated[UploadFile, File()],
    strategy: Annotated[str, Query(pattern="^(fail|skip)$")] = "fail",
) -> ImportResultRead:
    try:
        return PortabilityService(session).apply(
            await _import_content(file),
            strategy=strategy,
        )
    except ReleaseFeatureError as exc:
        raise _http_error(exc) from exc


@router.get("/audit-events", response_model=list[AuditEventRead])
def audit_events(
    session: SessionDependency,
    object_type: str | None = None,
    object_id: str | None = None,
    action: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 200,
) -> list[AuditEventRead]:
    return PortabilityService(session).audit_events(
        object_type=object_type,
        object_id=object_id,
        action=action,
        limit=limit,
    )


@router.get("/guided-setup/drafts", response_model=list[GuidedSetupDraftRead])
def guided_drafts(session: SessionDependency) -> list[GuidedSetupDraftRead]:
    return GuidedSetupService(session).list()


@router.post(
    "/guided-setup/drafts",
    response_model=GuidedSetupDraftRead,
    status_code=status.HTTP_201_CREATED,
)
def create_guided_draft(
    payload: GuidedSetupDraftWrite,
    session: SessionDependency,
) -> GuidedSetupDraftRead:
    return GuidedSetupService(session).create(payload)


@router.put("/guided-setup/drafts/{draft_id}", response_model=GuidedSetupDraftRead)
def update_guided_draft(
    draft_id: UUID,
    payload: GuidedSetupDraftWrite,
    session: SessionDependency,
) -> GuidedSetupDraftRead:
    try:
        return GuidedSetupService(session).update(draft_id, payload)
    except ReleaseFeatureError as exc:
        raise _http_error(exc) from exc


@router.get(
    "/guided-setup/drafts/{draft_id}/preview",
    response_model=GuidedSetupPreviewRead,
)
def guided_preview(
    draft_id: UUID,
    session: SessionDependency,
) -> GuidedSetupPreviewRead:
    try:
        return GuidedSetupService(session).preview(draft_id)
    except ReleaseFeatureError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/guided-setup/drafts/{draft_id}/apply",
    response_model=GuidedSetupApplyRead,
)
def guided_apply(
    draft_id: UUID,
    session: SessionDependency,
) -> GuidedSetupApplyRead:
    try:
        return GuidedSetupService(session).apply(draft_id)
    except ReleaseFeatureError as exc:
        raise _http_error(exc) from exc


@router.get("/fritzbox/devices", response_model=list[FritzBoxDeviceRead])
def fritzbox_devices(session: SessionDependency) -> list[FritzBoxDeviceRead]:
    setting = session.exec(
        select(IntegrationSetting).where(IntegrationSetting.kind == "fritzbox")
    ).first()
    if (
        setting is None
        or not setting.enabled
        or not setting.base_url
        or not setting.account
        or not setting.secret
    ):
        raise HTTPException(status_code=409, detail="FRITZ!Box ist nicht vollständig konfiguriert")
    try:
        devices = FritzBoxConnector(
            base_url=setting.base_url,
            account=setting.account,
            secret=setting.secret,
        ).devices()
        NetworkService(session).sync_observed_addresses(devices)
        return devices
    except FritzBoxConnectorError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
