"""FastAPI-приложение TMS/WMTS."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from pointcloud_tile import __version__
from pointcloud_tile.api.routes import metadata, tms, wmts
from pointcloud_tile.cache import TileCache
from pointcloud_tile.config import Settings, get_settings
from pointcloud_tile.storage import create_storage


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.settings = settings
    app.state.storage = create_storage(settings)
    app.state.cache = TileCache(settings)
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    cfg = settings or get_settings()
    app = FastAPI(
        title=cfg.app_name,
        version=__version__,
        description="Тайловый сервис для облаков точек (TMS/WMTS)",
        lifespan=lifespan,
    )
    app.include_router(tms.router, tags=["TMS"])
    app.include_router(wmts.router, tags=["WMTS"])
    app.include_router(metadata.router, tags=["Metadata"])
    return app
