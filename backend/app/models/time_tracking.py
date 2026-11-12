"""Persistent work intervals, with one database-enforced active timer."""

from uuid import uuid4

from sqlalchemy import Index, text
from sqlmodel import Field, SQLModel


class WorkInterval(SQLModel, table=True):
    __tablename__ = "work_intervals"
    __table_args__ = (
        Index("uq_work_interval_running", "running", unique=True, sqlite_where=text("running = 1")),
    )

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    ticket: str = Field(max_length=100, index=True)
    customer: str = Field(max_length=200)
    info: str = Field(default="", max_length=4000)
    started_at: float
    ended_at: float | None = None
    running: bool = True
    completed: bool = False
