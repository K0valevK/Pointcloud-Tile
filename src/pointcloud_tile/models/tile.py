"""Модели тайлов и пространственных координат."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TileCoord:
    """Координаты тайла в пространственном индексе."""

    z: int
    x: int
    y: int
    lod: int = 0

    def path_segment(self) -> str:
        return f"{self.z}/{self.x}/{self.y}/lod{self.lod}"


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """Ограничивающий прямоугольник в системе координат слоя."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float
    min_z: float | None = None
    max_z: float | None = None
    crs: str = "EPSG:4326"

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y


@dataclass(frozen=True, slots=True)
class TileFilter:
    """Фильтрация точек по атрибутам (параметры запроса API)."""

    intensity_min: float | None = None
    intensity_max: float | None = None
    classification: list[int] | None = None
    height_min: float | None = None
    height_max: float | None = None
