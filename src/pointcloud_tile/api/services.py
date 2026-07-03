"""Сервис раздачи тайлов (общая логика TMS/WMTS)."""

from fastapi import HTTPException, Request
from fastapi.responses import Response

from pointcloud_tile.api.schemas import TileQueryParams
from pointcloud_tile.models.tile import TileCoord, TileFilter

def parse_tile_filter(params: TileQueryParams) -> TileFilter:
    classification = None
    if params.classification:
        classification = [int(c.strip()) for c in params.classification.split(",") if c.strip()]
    return TileFilter(
        intensity_min=params.intensity_min,
        intensity_max=params.intensity_max,
        classification=classification,
        height_min=params.height_min,
        height_max=params.height_max,
    )


def get_tile_response(
    request: Request,
    layer: str,
    z: int,
    x: int,
    y: int,
    tile_format: str,
    params: TileQueryParams,
) -> Response:
    """Загружает тайл из кэша или хранилища."""
    settings = request.app.state.settings
    storage = request.app.state.storage
    cache = request.app.state.cache
    filters = parse_tile_filter(params)
    coord = TileCoord(z=z, x=x, y=y, lod=params.lod)

    cached = cache.get(layer, coord, tile_format, filters)
    if cached:
        media_type = "application/octet-stream" if tile_format == "bin" else "application/vnd.laz"
        return Response(content=cached, media_type=media_type)

    if not storage.exists(layer, coord):
        raise HTTPException(status_code=404, detail=f"Tile not found: {layer}/{coord.path_segment()}")

    data = storage.read_tile(layer, coord)

    # Фильтрация по атрибутам — заглушка для последующей реализации
    if tile_format == "bin" and filters != TileFilter():
        pass  # TODO: decode LAZ, apply filters, re-encode

    cache.set(layer, coord, tile_format, data, filters)
    media_type = "application/octet-stream" if tile_format == "bin" else "application/vnd.laz"
    return Response(content=data, media_type=media_type)
