from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.quality import QualityReportRead
from app.services.quality import QualityError, QualityNotFoundError, QualityService

router = APIRouter(prefix="/quality", tags=["quality"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("/latest", response_model=QualityReportRead)
def latest_quality_report(session: SessionDependency) -> QualityReportRead:
    try:
        return QualityService(session).latest()
    except QualityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except QualityError as exc:
        raise HTTPException(
            status_code=500,
            detail="Qualitätsbericht konnte nicht geladen werden",
        ) from exc


@router.post("/run", response_model=QualityReportRead, status_code=status.HTTP_201_CREATED)
def run_quality_report(session: SessionDependency) -> QualityReportRead:
    try:
        return QualityService(session).run(trigger="manual")
    except QualityError as exc:
        raise HTTPException(
            status_code=500,
            detail="Qualitätsprüfung ist fehlgeschlagen",
        ) from exc
