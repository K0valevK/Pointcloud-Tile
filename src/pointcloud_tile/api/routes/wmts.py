"""WMTS-эндпоинты (GetCapabilities, GetTile, GetFeatureInfo)."""

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response

from pointcloud_tile import __version__
from pointcloud_tile.api.schemas import TileQueryParams
from pointcloud_tile.api.services import get_tile_response

router = APIRouter(prefix="/wmts")


@router.get("")
async def wmts_dispatcher(
    request: Request,
    service: str = Query(default="WMTS"),
    request_type: str = Query(alias="REQUEST"),
    version: str = Query(default="1.0.0"),
    layer: str | None = Query(default=None),
    style: str | None = Query(default=None),
    tilematrixset: str | None = Query(default=None),
    tilematrix: str | None = Query(default=None),
    tilerow: int | None = Query(default=None),
    tilecol: int | None = Query(default=None),
    format: str | None = Query(default="laz"),
    i: float | None = Query(default=None),
    j: float | None = Query(default=None),
    lod: int = Query(default=0, ge=0, le=9),
):
    """WMTS KVP-интерфейс."""
    req = request_type.upper()

    if req == "GETCAPABILITIES":
        return _get_capabilities(version)

    if req == "GETTILE":
        if None in (layer, tilematrix, tilerow, tilecol, format):
            from fastapi import HTTPException

            raise HTTPException(status_code=400, detail="Missing GetTile parameters")
        z = int(tilematrix.replace("EPSG:4326:", "").replace("z", "")) if tilematrix else 0
        params = TileQueryParams(lod=lod)
        return get_tile_response(
            request,
            layer,
            z,
            tilecol,
            tilerow,
            format.replace("image/", ""),
            params,
        )

    if req == "GETFEATUREINFO":
        return Response(
            content='{"points":[],"message":"GetFeatureInfo stub"}',
            media_type="application/json",
        )

    from fastapi import HTTPException

    raise HTTPException(status_code=400, detail=f"Unknown REQUEST: {request_type}")


def _get_capabilities(version: str) -> Response:
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Capabilities version="{version}" xmlns="http://www.opengis.net/wmts/1.0">
  <ServiceIdentification>
    <Title>Pointcloud-Tile WMTS</Title>
    <ServiceType>OGC WMTS</ServiceType>
    <ServiceTypeVersion>{version}</ServiceTypeVersion>
  </ServiceIdentification>
  <Contents>
    <Layer>
      <Identifier>pointcloud</Identifier>
      <Format>application/vnd.laz</Format>
      <Format>application/octet-stream</Format>
      <TileMatrixSetLink><TileMatrixSet>EPSG:4326</TileMatrixSet></TileMatrixSetLink>
    </Layer>
    <TileMatrixSet>
      <Identifier>EPSG:4326</Identifier>
      <SupportedCRS>EPSG:4326</SupportedCRS>
    </TileMatrixSet>
  </Contents>
  <VendorSpecificCapabilities>
    <Extension type="pointcloud" version="{__version__}">
      <LoDLevels>0,1,2,3,4</LoDLevels>
      <TileFormats>laz,bin</TileFormats>
    </Extension>
  </VendorSpecificCapabilities>
</Capabilities>"""
    return Response(content=xml, media_type="application/xml")
