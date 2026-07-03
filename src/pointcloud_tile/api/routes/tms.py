"""TMS-эндпоинты."""

from fastapi import APIRouter, Query, Request

from pointcloud_tile.api.schemas import TileQueryParams
from pointcloud_tile.api.services import get_tile_response

router = APIRouter(prefix="/tms")


@router.get("/{version}/{layer}/{z}/{x}/{y}.{fmt}")
async def get_tms_tile(
    request: Request,
    version: str,
    layer: str,
    z: int,
    x: int,
    y: int,
    fmt: str,
    intensity_min: float | None = Query(default=None),
    intensity_max: float | None = Query(default=None),
    classification: str | None = Query(default=None),
    height_min: float | None = Query(default=None),
    height_max: float | None = Query(default=None),
    lod: int = Query(default=0, ge=0, le=9),
):
    """
    TMS: GET /tms/{version}/{layer}/{z}/{x}/{y}.{format}

    Поддерживаемые форматы: laz, bin
    """
    if fmt not in {"laz", "bin"}:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")

    params = TileQueryParams(
        intensity_min=intensity_min,
        intensity_max=intensity_max,
        classification=classification,
        height_min=height_min,
        height_max=height_max,
        lod=lod,
    )
    return get_tile_response(request, layer, z, x, y, fmt, params)
