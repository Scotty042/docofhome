"""Server-clock timers survive refreshes and application restarts."""

import time
from typing import Annotated, Any, Literal, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.db.session import get_session
from app.models.time_tracking import WorkInterval

router = APIRouter(prefix="/time-tracking", tags=["time-tracking"])
SessionDep = Annotated[Session, Depends(get_session)]


class StartRequest(BaseModel):
    ticket: str = Field(min_length=1, max_length=100)
    customer: str = Field(min_length=1, max_length=200)
    info: str = Field(default="", max_length=4000)

    @field_validator("ticket", "customer", "info", mode="before")
    @classmethod
    def trim(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


@router.get("", response_model=list[WorkInterval])
def list_intervals(session: SessionDep) -> list[WorkInterval]:
    return list(
        session.exec(select(WorkInterval).order_by(col(WorkInterval.started_at).desc())).all()
    )


@router.post("/start", response_model=WorkInterval, status_code=201)
def start(data: StartRequest, session: SessionDep) -> WorkInterval:
    interval = WorkInterval(**data.model_dump(), started_at=time.time())
    session.add(interval)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            409, "Bitte den laufenden Arbeitslauf zuerst pausieren oder beenden."
        ) from exc
    session.refresh(interval)
    return interval


@router.post("/{interval_id}/{action}", response_model=WorkInterval)
def stop(interval_id: str, action: Literal["pause", "end"], session: SessionDep) -> WorkInterval:
    result = session.execute(
        update(WorkInterval)
        .where(
            col(WorkInterval.id) == interval_id,
            col(WorkInterval.running).is_(True),
        )
        .values(ended_at=time.time(), running=False, completed=action == "end")
    )
    if cast(CursorResult[Any], result).rowcount != 1:
        session.rollback()
        raise HTTPException(
            409, "Dieser Arbeitslauf läuft nicht mehr. Bitte Ansicht aktualisieren."
        )
    session.commit()
    interval = session.get(WorkInterval, interval_id)
    assert interval is not None
    return interval
