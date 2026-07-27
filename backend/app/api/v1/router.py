from fastapi import APIRouter

from app.api.v1 import (
    about,
    archive,
    asset_engine,
    backups,
    consumption,
    document_links,
    documents,
    electrical,
    electrical_circuits,
    electrical_topology,
    energy,
    health,
    home_assistant,
    immich,
    knowledge,
    network,
    quality,
    release,
    search,
    settings,
    smart_meter,
    system,
    work,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(about.router)
api_router.include_router(health.router)
api_router.include_router(system.router)
api_router.include_router(settings.router)
api_router.include_router(backups.router)
api_router.include_router(documents.router)
api_router.include_router(document_links.router)
api_router.include_router(consumption.router)
api_router.include_router(knowledge.router)
api_router.include_router(network.router)
api_router.include_router(work.router)
api_router.include_router(quality.router)
api_router.include_router(release.router)
api_router.include_router(home_assistant.router)
api_router.include_router(immich.router)
api_router.include_router(archive.router)
api_router.include_router(search.router)
api_router.include_router(asset_engine.router)
api_router.include_router(electrical.router)
api_router.include_router(electrical_circuits.router)
api_router.include_router(electrical_topology.router)
api_router.include_router(smart_meter.router)
api_router.include_router(energy.router)
