"""Server-clock timers survive refreshes and application restarts."""

import time
from datetime import datetime
from typing import Annotated, Any, Literal, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator
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
    session.connection().exec_driver_sql("BEGIN IMMEDIATE")
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


class IntervalWrite(StartRequest):
    started_at: datetime
    ended_at: datetime

    @model_validator(mode="after")
    def valid_times(self) -> "IntervalWrite":
        if self.started_at.tzinfo is None or self.ended_at.tzinfo is None:
            raise ValueError("Anfang und Ende müssen eine Zeitzone enthalten.")
        if self.ended_at <= self.started_at:
            raise ValueError("Ende muss nach Anfang liegen.")
        if self.ended_at.timestamp() > time.time():
            raise ValueError("Arbeitszeiten dürfen nicht in der Zukunft liegen.")
        return self


def save_interval(
    data: IntervalWrite, session: Session, interval_id: str | None = None
) -> WorkInterval:
    # Reserve the SQLite writer before checking overlaps, including concurrent requests.
    session.connection().exec_driver_sql("BEGIN IMMEDIATE")
    row = session.get(WorkInterval, interval_id) if interval_id else None
    if interval_id and row is None:
        raise HTTPException(404, "Arbeitslauf nicht gefunden.")
    if row is not None and row.running:
        raise HTTPException(409, "Bitte den laufenden Arbeitslauf zuerst pausieren oder beenden.")
    start, end = data.started_at.timestamp(), data.ended_at.timestamp()
    overlap = select(WorkInterval).where(
        col(WorkInterval.started_at) < end,
        (col(WorkInterval.ended_at).is_(None)) | (col(WorkInterval.ended_at) > start),
    )
    if row is not None:
        overlap = overlap.where(col(WorkInterval.id) != row.id)
    if session.exec(overlap).first() is not None:
        raise HTTPException(409, "Der Zeitraum überschneidet sich mit einem anderen Arbeitslauf.")
    if row is None:
        row = WorkInterval(
            ticket=data.ticket,
            customer=data.customer,
            started_at=start,
            running=False,
            completed=True,
        )
    row.ticket, row.customer, row.info = data.ticket, data.customer, data.info
    row.started_at, row.ended_at = start, end
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


@router.post("/manual", response_model=WorkInterval, status_code=201)
def create_manual(data: IntervalWrite, session: SessionDep) -> WorkInterval:
    return save_interval(data, session)


@router.put("/{interval_id}", response_model=WorkInterval)
def edit_interval(interval_id: str, data: IntervalWrite, session: SessionDep) -> WorkInterval:
    return save_interval(data, session, interval_id)


@router.delete("/{interval_id}", status_code=204)
def delete_interval(interval_id: str, session: SessionDep) -> None:
    """Delete one closed interval; never discard an active timer."""
    session.connection().exec_driver_sql("BEGIN IMMEDIATE")
    row = session.get(WorkInterval, interval_id)
    if row is None:
        raise HTTPException(404, "Arbeitslauf nicht gefunden.")
    if row.running:
        raise HTTPException(409, "Bitte den laufenden Arbeitslauf zuerst pausieren oder beenden.")
    session.delete(row)
    session.commit()
