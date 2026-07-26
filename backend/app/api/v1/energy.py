from collections.abc import Callable
from typing import Annotated, TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.energy import (
    EnergyBalanceRead,
    EnergyComponentRead,
    EnergyComponentWrite,
    EnergyConfigurationRead,
    EnergyConfigurationWrite,
)
from app.services.energy import (
    EnergyConflictError,
    EnergyError,
    EnergyNotFoundError,
    EnergyService,
    EnergyValidationError,
)

router = APIRouter(prefix="/energy", tags=["energy"])
SessionDependency = Annotated[Session, Depends(get_session)]
T = TypeVar("T")


def _call(callback: Callable[[], T]) -> T:
    try:
        return callback()
    except EnergyNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except EnergyConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except EnergyValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except EnergyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Energiedaten konnten nicht verarbeitet werden",
        ) from exc


@router.get("/configuration", response_model=EnergyConfigurationRead)
def get_configuration(session: SessionDependency) -> EnergyConfigurationRead:
    return _call(lambda: EnergyService(session).get_configuration())


@router.put("/configuration", response_model=EnergyConfigurationRead)
def update_configuration(
    payload: EnergyConfigurationWrite,
    session: SessionDependency,
) -> EnergyConfigurationRead:
    return _call(lambda: EnergyService(session).update_configuration(payload))


@router.get("/components", response_model=list[EnergyComponentRead])
def list_components(
    session: SessionDependency,
    include_archived: bool = False,
) -> list[EnergyComponentRead]:
    return _call(
        lambda: EnergyService(session).list_components(include_archived=include_archived)
    )


@router.post(
    "/components",
    response_model=EnergyComponentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_component(
    payload: EnergyComponentWrite,
    session: SessionDependency,
) -> EnergyComponentRead:
    return _call(lambda: EnergyService(session).create_component(payload))


@router.put("/components/{component_id}", response_model=EnergyComponentRead)
def update_component(
    component_id: UUID,
    payload: EnergyComponentWrite,
    session: SessionDependency,
) -> EnergyComponentRead:
    return _call(lambda: EnergyService(session).update_component(component_id, payload))


@router.delete("/components/{component_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_component(component_id: UUID, session: SessionDependency) -> Response:
    _call(lambda: EnergyService(session).archive_component(component_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/balance", response_model=EnergyBalanceRead)
def balance(
    session: SessionDependency,
    months: Annotated[int, Query(ge=1, le=60)] = 12,
) -> EnergyBalanceRead:
    return _call(lambda: EnergyService(session).balance(months=months))
