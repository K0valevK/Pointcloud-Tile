"""Метаданные слоя облака точек."""

from dataclasses import dataclass, field

from pointcloud_tile.models.tile import BoundingBox


@dataclass(slots=True)
class LayerMetadata:
    """Метаданные тайлового слоя для TMS/WMTS GetCapabilities."""

    name: str
    title: str
    abstract: str
    bbox: BoundingBox
    min_zoom: int = 0
    max_zoom: int = 18
    lod_levels: list[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])
    point_count: int = 0
    tile_formats: list[str] = field(default_factory=lambda: ["laz", "bin"])
    source_crs: str = "EPSG:4326"
    tile_matrix_set: str = "EPSG:4326"
