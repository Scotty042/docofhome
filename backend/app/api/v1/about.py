from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.about import AboutRead, FeedbackResultRead, FeedbackWrite
from app.services.about import (
    AboutService,
    FeedbackRateLimitError,
    FeedbackUnavailableError,
)

router = APIRouter(prefix="/about", tags=["about"])
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("", response_model=AboutRead)
def read_about(session: SessionDependency) -> AboutRead:
    return AboutService(session).read()


@router.post(
    "/feedback",
    response_model=FeedbackResultRead,
    status_code=status.HTTP_201_CREATED,
)
def submit_feedback(
    payload: FeedbackWrite,
    request: Request,
    session: SessionDependency,
) -> FeedbackResultRead:
    client_key = request.client.host if request.client else "unknown"
    try:
        return AboutService(session).submit_feedback(payload, client_key)
    except FeedbackUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except FeedbackRateLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
