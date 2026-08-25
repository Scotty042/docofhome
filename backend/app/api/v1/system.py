from fastapi import APIRouter

from app.core.settings import settings

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/info")
def system_info() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "slogan": "Know your home.",
    }
