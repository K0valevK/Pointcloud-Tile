"""Запись тайлов в хранилище и чекпоинты."""

import json
from pathlib import Path

import numpy as np

from pointcloud_tile.config import Settings
from pointcloud_tile.models.tile import TileCoord
from pointcloud_tile.storage.base import TileStorage
from pointcloud_tile.tiling.index import QuadTreeIndex
from pointcloud_tile.tiling.lod import LoDGenerator


class TilingPipeline:
    """Полный конвейер тайлирования с поддержкой возобновления."""

    def __init__(
        self,
        settings: Settings,
        storage: TileStorage,
        lod_levels: int | None = None,
    ) -> None:
        self.settings = settings
        self.storage = storage
        self.lod_generator = LoDGenerator(num_levels=lod_levels or settings.lod_levels)
        self.index = QuadTreeIndex()

    def tile_layer(
        self,
        layer_name: str,
        points: np.ndarray,
        resume: bool = True,
    ) -> dict:
        """Нарезает облако на тайлы и записывает LoD-пирамиду."""
        checkpoint_path = self.settings.checkpoint_dir / f"{layer_name}.json"
        completed: set[str] = set()

        if resume and checkpoint_path.exists():
            data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            completed = set(data.get("completed_tiles", []))

        root = self.index.build(points)
        tile_coords = self.index.iter_tiles(root)
        written = 0

        for coord in tile_coords:
            key = f"{coord.path_segment()}"
            if key in completed:
                continue

            indices = self.index.query_tile(root, coord)
            tile_points = points[indices]
            lod_levels = self.lod_generator.generate(tile_points)

            for lod, lod_points in lod_levels.items():
                lod_coord = TileCoord(z=coord.z, x=coord.x, y=coord.y, lod=lod)
                self.storage.write_tile_atomic(layer_name, lod_coord, lod_points)

            completed.add(key)
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            checkpoint_path.write_text(
                json.dumps({"completed_tiles": sorted(completed)}),
                encoding="utf-8",
            )
            written += 1

        if checkpoint_path.exists():
            checkpoint_path.unlink()

        return {"layer": layer_name, "tiles_written": written, "total_tiles": len(tile_coords)}
