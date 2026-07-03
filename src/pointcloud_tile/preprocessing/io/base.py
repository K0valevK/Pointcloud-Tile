"""Абстрактные интерфейсы чтения и записи облаков точек."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pointcloud_tile.preprocessing.models.enums import PointCloudFormat
    from pointcloud_tile.preprocessing.models.metadata import PointCloudHeader
    from pointcloud_tile.preprocessing.models.point_cloud import PointCloud


class BaseReader(ABC):
    """Базовый интерфейс чтения облаков точек."""

    format: PointCloudFormat

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        if not self.path.exists():
            from pointcloud_tile.preprocessing.exceptions import ReaderError

            raise ReaderError(self.path, "File does not exist")

    @abstractmethod
    def read_header(self) -> PointCloudHeader:
        """Читает заголовок без полной загрузки точек (если поддерживается)."""

    @abstractmethod
    def read(self) -> PointCloud:
        """Загружает всё облако точек в память."""

    @abstractmethod
    def iter_chunks(self, chunk_size: int = 1_000_000) -> Iterator[PointCloud]:
        """Потоковое чтение блоками фиксированного размера."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.path!s})"


class BaseWriter(ABC):
    """Базовый интерфейс записи облаков точек."""

    format: PointCloudFormat

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    @abstractmethod
    def write(self, point_cloud: PointCloud) -> Path:
        """Записывает облако точек в файл; возвращает путь."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.path!s})"
