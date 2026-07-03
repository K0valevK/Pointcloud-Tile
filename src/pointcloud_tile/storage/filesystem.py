"""Хранение тайлов в локальной файловой системе."""

import os
import tempfile
from pathlib import Path

import numpy as np

from pointcloud_tile.models.tile import TileCoord
from pointcloud_tile.storage.base import TileStorage
from pointcloud_tile.storage.encoder import encode_points_laz


class FilesystemTileStorage(TileStorage):
    """Файловое хранилище с атомарной записью через временный файл."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, layer: str, coord: TileCoord) -> Path:
        return self.base_dir / self.tile_key(layer, coord)

    def write_tile_atomic(self, layer: str, coord: TileCoord, points: np.ndarray) -> str:
        target = self._path(layer, coord)
        target.parent.mkdir(parents=True, exist_ok=True)
        data = encode_points_laz(points)

        fd, tmp_path = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as tmp:
                tmp.write(data)
            os.replace(tmp_path, target)
        except Exception:
            Path(tmp_path).unlink(missing_ok=True)
            raise

        return str(target)

    def read_tile(self, layer: str, coord: TileCoord) -> bytes:
        path = self._path(layer, coord)
        if not path.exists():
            msg = f"Tile not found: {path}"
            raise FileNotFoundError(msg)
        return path.read_bytes()

    def exists(self, layer: str, coord: TileCoord) -> bool:
        return self._path(layer, coord).exists()

    def delete_layer(self, layer: str) -> None:
        layer_dir = self.base_dir / layer
        if layer_dir.exists():
            import shutil

            shutil.rmtree(layer_dir)
