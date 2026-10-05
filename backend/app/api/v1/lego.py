from collections.abc import Callable
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.lego import LegoDashboard, LegoSetRead, LegoSetWrite
from app.services.lego import LegoConflictError, LegoService

router = APIRouter(prefix="/lego", tags=["lego"])
SessionDep = Annotated[Session, Depends(get_session)]


def translated[T](operation: Callable[[], T]) -> T:
    try:
        return operation()
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except LegoConflictError as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/dashboard", response_model=LegoDashboard)
def dashboard(session: SessionDep) -> LegoDashboard:
    return LegoService(session).dashboard()


@router.get("/sets")
def search(
    session: SessionDep,
    q: str = Query(default="", max_length=200),
    set_number: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> dict[str, Any]:
    return translated(lambda: LegoService(session).search(q, set_number, offset, limit))


@router.post("/sets", response_model=LegoSetRead, status_code=201)
def create(data: LegoSetWrite, session: SessionDep) -> LegoSetRead:
    return translated(lambda: LegoService(session).save(data))


@router.get("/sets/{set_id}", response_model=LegoSetRead)
def get(set_id: UUID, session: SessionDep) -> LegoSetRead:
    service = LegoService(session)
    return translated(lambda: service.read(service.get(set_id)))


@router.put("/sets/{set_id}", response_model=LegoSetRead)
def update(set_id: UUID, data: LegoSetWrite, session: SessionDep) -> LegoSetRead:
    return translated(lambda: LegoService(session).save(data, set_id))


@router.delete("/sets/{set_id}", status_code=204)
def delete(set_id: UUID, session: SessionDep) -> None:
    translated(lambda: LegoService(session).delete(set_id))
