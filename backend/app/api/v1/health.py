from pathlib import Path

from fastapi import APIRouter
from sqlmodel import text

from app.core.settings import settings
from app.db.session import engine

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check() -> dict[str, str]:
    """Liveness endpoint without external integration checks."""

    return {"status": "ok", "name": settings.app_name, "version": settings.app_version}


@router.get("/ready")
def readiness_check() -> dict[str, str]:
    """Readiness endpoint that verifies persistent storage and SQLite access."""

    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ready"}
