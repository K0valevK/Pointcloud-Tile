"""Pydantic-схемы API."""

from pydantic import BaseModel, Field


class LayerInfoResponse(BaseModel):
    name: str
    title: str
    abstract: str
    bbox: list[float] = Field(description="[min_x, min_y, max_x, max_y]")
    crs: str
    lod_levels: list[int]
    point_count: int
    tile_formats: list[str]


class TileQueryParams(BaseModel):
    intensity_min: float | None = None
    intensity_max: float | None = None
    classification: str | None = Field(default=None, description="Comma-separated class IDs")
    height_min: float | None = None
    height_max: float | None = None
    lod: int = Field(default=0, ge=0, le=9)
