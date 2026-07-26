from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.settings import (
    ConfigurationRead,
    ConfigurationWrite,
    IntegrationKind,
    IntegrationTestResult,
    IntegrationWrite,
    SetupStatusRead,
)
from app.services.integration_checks import IntegrationCheckService
from app.services.settings import (
    InvalidIntegrationError,
    SettingsService,
    SetupAlreadyCompletedError,
    SetupNotCompletedError,
)

router = APIRouter(tags=["settings"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("/setup/status", response_model=SetupStatusRead)
def setup_status(session: SessionDependency) -> SetupStatusRead:
    return SettingsService(session).get_setup_status()


@router.post(
    "/setup/complete",
    response_model=ConfigurationRead,
    status_code=status.HTTP_201_CREATED,
)
def complete_setup(payload: ConfigurationWrite, session: SessionDependency) -> ConfigurationRead:
    try:
        return SettingsService(session).complete_setup(payload)
    except SetupAlreadyCompletedError as exc:
        raise HTTPException(status_code=409, detail="Setup has already been completed") from exc
    except InvalidIntegrationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/settings", response_model=ConfigurationRead)
def read_settings(session: SessionDependency) -> ConfigurationRead:
    try:
        return SettingsService(session).get_configuration()
    except SetupNotCompletedError as exc:
        raise HTTPException(status_code=404, detail="Setup has not been completed") from exc


@router.put("/settings", response_model=ConfigurationRead)
def update_settings(
    payload: ConfigurationWrite,
    session: SessionDependency,
) -> ConfigurationRead:
    try:
        return SettingsService(session).update_configuration(payload)
    except SetupNotCompletedError as exc:
        raise HTTPException(
            status_code=409,
            detail="Complete setup before editing settings",
        ) from exc
    except InvalidIntegrationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post(
    "/settings/integrations/{kind}/test",
    response_model=IntegrationTestResult,
)
def test_integration(
    kind: IntegrationKind,
    session: SessionDependency,
) -> IntegrationTestResult:
    """Test the stored integration configuration without changing the remote service."""
    return IntegrationCheckService(session).check(kind)


@router.post(
    "/settings/integrations/test",
    response_model=IntegrationTestResult,
)
def test_integration_payload(
    payload: IntegrationWrite,
    session: SessionDependency,
) -> IntegrationTestResult:
    """Test unsaved integration credentials during first setup without persisting them."""
    return IntegrationCheckService(session).check_payload(payload)
