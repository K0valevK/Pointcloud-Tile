"""Метаданные облака точек."""

from dataclasses import dataclass, field
from typing import Any

from pointcloud_tile.preprocessing.models.enums import PointCloudFormat


@dataclass(frozen=True, slots=True)
class AxisAlignedBoundingBox:
    """Ограничивающий параллелепипед (AABB)."""

    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float

    @classmethod
    def from_arrays(
        cls,
        x: Any,
        y: Any,
        z: Any,
    ) -> "AxisAlignedBoundingBox":
        return cls(
            min_x=float(min(x)),
            min_y=float(min(y)),
            min_z=float(min(z)),
            max_x=float(max(x)),
            max_y=float(max(y)),
            max_z=float(max(z)),
        )

    def as_tuple(self) -> tuple[float, float, float, float, float, float]:
        return (self.min_x, self.min_y, self.min_z, self.max_x, self.max_y, self.max_z)


@dataclass(frozen=True, slots=True)
class PointCloudHeader:
    """Заголовок файла облака точек (без загрузки всех точек)."""

    point_count: int
    format: PointCloudFormat
    crs: str | None = None
    bbox: AxisAlignedBoundingBox | None = None
    point_format_id: int | None = None
    version: str | None = None
    source_path: str | None = None


@dataclass(slots=True)
class PointCloudMetadata:
    """Метаданные экземпляра PointCloud в памяти."""

    source_path: str | None = None
    source_format: PointCloudFormat | None = None
    crs: str | None = None
    origin: tuple[float, float, float] | None = None
    processed_point_count: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)
