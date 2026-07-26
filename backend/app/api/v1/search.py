from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.search import SearchResponseRead
from app.services.search import GlobalSearchService, SearchServiceError

router = APIRouter(prefix="/search", tags=["search"])
SessionDependency = Annotated[Session, Depends(get_session)]
SearchQuery = Annotated[str, Query(min_length=1, max_length=100)]
SearchLimit = Annotated[int, Query(ge=1, le=20)]


@router.get("", response_model=SearchResponseRead)
def global_search(
    session: SessionDependency,
    q: SearchQuery,
    limit_per_type: SearchLimit = 5,
    include_archived: bool = False,
) -> SearchResponseRead:
    try:
        return GlobalSearchService(session).search(
            q,
            limit_per_type=limit_per_type,
            include_archived=include_archived,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SearchServiceError as exc:
        raise HTTPException(
            status_code=500,
            detail="Die globale Suche ist derzeit nicht verfügbar.",
        ) from exc
