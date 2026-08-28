import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import electrical_layout
from app.api.v1.router import api_router
from app.core.settings import settings
from app.mcp_server import mcp_http_app, mcp_server
from app.services.backup_schedule import backup_scheduler_loop
from app.services.quality_schedule import quality_scheduler_loop
from app.services.docker_sync_schedule import docker_sync_scheduler_loop


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Prepare persistent paths and run lightweight background maintenance."""

    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    (settings.data_dir / "uploads" / "product-images").mkdir(parents=True, exist_ok=True)
    (settings.data_dir / "uploads" / "recipe-images").mkdir(parents=True, exist_ok=True)
    scheduler_task = asyncio.create_task(backup_scheduler_loop())
    quality_task = asyncio.create_task(quality_scheduler_loop())
    docker_task = asyncio.create_task(docker_sync_scheduler_loop())
    try:
        async with mcp_server.session_manager.run():
            yield
    finally:
        scheduler_task.cancel()
        quality_task.cancel()
        docker_task.cancel()
        with suppress(asyncio.CancelledError):
            await scheduler_task
        with suppress(asyncio.CancelledError):
            await quality_task
        with suppress(asyncio.CancelledError):
            await docker_task


app = FastAPI(
    title="DocOfHome API",
    version=settings.app_version,
    description="API for the DocOfHome digital home twin.",
    lifespan=lifespan,
)
app.add_middleware(GZipMiddleware, minimum_size=1024, compresslevel=5)
app.include_router(api_router)
app.include_router(electrical_layout.router, prefix="/api/v1")
app.add_route("/mcp", mcp_http_app, methods=["GET", "POST", "DELETE"], name="mcp")
app.add_route("/mcp/{token}", mcp_http_app, methods=["GET", "POST", "DELETE"], name="mcp-token")

static_dir = settings.static_dir
assets_dir = static_dir / "assets"
if assets_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


def _safe_static_file(full_path: str) -> Path | None:
    """Resolve a frontend path while preventing traversal outside static_dir."""

    root = static_dir.resolve()
    requested = (root / full_path).resolve()
    if requested != root and root not in requested.parents:
        return None
    return requested if requested.is_file() else None


@app.get("/{full_path:path}", include_in_schema=False)
def frontend(full_path: str) -> FileResponse:
    # Unknown API routes must return JSON 404, never the SPA HTML fallback.
    if full_path == "api" or full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")

    requested = _safe_static_file(full_path)
    if requested is not None:
        return FileResponse(requested)

    index_file = static_dir / "index.html"
    if not index_file.is_file():
        raise HTTPException(status_code=503, detail="Frontend build is unavailable")
    return FileResponse(index_file)
