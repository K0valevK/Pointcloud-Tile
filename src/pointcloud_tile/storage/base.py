"""Абстракция хранилища тайлов."""

from abc import ABC, abstractmethod

import numpy as np

from pointcloud_tile.models.tile import TileCoord


class TileStorage(ABC):
    """Интерфейс хранилища тайлов (файловая система или S3)."""

    @abstractmethod
    def write_tile_atomic(self, layer: str, coord: TileCoord, points: np.ndarray) -> str:
        """Атомарно записывает тайл; возвращает URI/путь."""

    @abstractmethod
    def read_tile(self, layer: str, coord: TileCoord) -> bytes:
        """Читает бинарные данные тайла."""

    @abstractmethod
    def exists(self, layer: str, coord: TileCoord) -> bool:
        """Проверяет наличие тайла."""

    @abstractmethod
    def delete_layer(self, layer: str) -> None:
        """Удаляет все тайлы слоя (инвалидация кэша)."""

    def tile_key(self, layer: str, coord: TileCoord) -> str:
        return f"{layer}/{coord.path_segment()}.laz"
