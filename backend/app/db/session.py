from collections.abc import Generator

from sqlmodel import Session, create_engine

from app.core.settings import settings
from app.db import sqlite as _sqlite  # noqa: F401 - registers the connection listener

engine = create_engine(
    f"sqlite:///{settings.database_path}",
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)


def get_session() -> Generator[Session]:
    """Provide a database session for FastAPI dependencies."""

    with Session(engine) as session:
        yield session
