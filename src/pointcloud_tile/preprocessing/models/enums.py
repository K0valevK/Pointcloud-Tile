"""Перечисления модуля предобработки."""

from enum import Enum


class PointCloudFormat(str, Enum):
    """Поддерживаемые форматы облаков точек."""

    LAS = "las"
    LAZ = "laz"
    PLY = "ply"

    @classmethod
    def from_extension(cls, extension: str) -> "PointCloudFormat | None":
        ext = extension.lower().lstrip(".")
        for fmt in cls:
            if fmt.value == ext:
                return fmt
        return None

    @property
    def extension(self) -> str:
        return f".{self.value}"
