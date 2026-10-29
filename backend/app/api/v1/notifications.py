from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.notifications import Provider, PushDeliveryRead, PushRead, PushResult, PushWrite
from app.services.notifications import PushError, PushService


class SecretSafeRoute(APIRoute):
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original = super().get_route_handler()

        async def safe(request: Request) -> Response:
            try:
                return await original(request)
            except RequestValidationError as exc:
                return JSONResponse(
                    status_code=422,
                    content={
                        "detail": [
                            {key: error[key] for key in ("loc", "msg", "type")}
                            for error in exc.errors()
                        ]
                    },
                )

        return safe


router = APIRouter(
    prefix="/settings/notifications", tags=["notifications"], route_class=SecretSafeRoute
)
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=PushRead)
def read(session: SessionDep) -> PushRead:
    return PushService(session).read()


@router.put("", response_model=PushRead)
def save(payload: PushWrite, session: SessionDep) -> PushRead:
    try:
        return PushService(session).save(payload)
    except PushError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/history", response_model=list[PushDeliveryRead])
def history(session: SessionDep) -> list[PushDeliveryRead]:
    return PushService(session).history()


@router.post("/test/{provider}", response_model=PushResult)
def test(provider: Provider, payload: PushWrite, session: SessionDep) -> PushResult:
    try:
        success = PushService(session).test(provider, payload)
        return PushResult(
            success=success,
            message="Testnachricht vom Dienst angenommen"
            if success
            else "Test fehlgeschlagen – siehe Versandstatus",
        )
    except PushError as exc:
        raise HTTPException(422, str(exc)) from exc
