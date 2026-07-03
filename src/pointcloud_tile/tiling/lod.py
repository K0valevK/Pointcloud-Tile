"""Генерация уровней детализации (LoD 0–4)."""

import numpy as np

from pointcloud_tile.preprocessing.filters import preserve_extremes


class LoDGenerator:
    """Пирамида LoD методом voxel-grid downsampling с сохранением экстремумов."""

    def __init__(self, num_levels: int = 5, voxel_size_factor: float = 2.0) -> None:
        self.num_levels = num_levels
        self.voxel_size_factor = voxel_size_factor

    def generate(self, points: np.ndarray) -> dict[int, np.ndarray]:
        """Строит LoD 0..N-1 для набора точек."""
        levels: dict[int, np.ndarray] = {0: points}
        current = points

        for lod in range(1, self.num_levels):
            voxel_size = self._estimate_voxel_size(current) * (self.voxel_size_factor**lod)
            downsampled = self._voxel_downsample(current, voxel_size)
            downsampled = preserve_extremes(current, downsampled)
            levels[lod] = downsampled
            current = downsampled

        return levels

    def _estimate_voxel_size(self, points: np.ndarray) -> float:
        if len(points) < 2:
            return 1.0
        extent = max(
            points[:, 0].max() - points[:, 0].min(),
            points[:, 1].max() - points[:, 1].min(),
            points[:, 2].max() - points[:, 2].min(),
        )
        target = max(100, len(points) // 10)
        return max(extent / target, 0.01)

    def _voxel_downsample(self, points: np.ndarray, voxel_size: float) -> np.ndarray:
        if len(points) == 0:
            return points

        coords = np.floor(points[:, :3] / voxel_size).astype(np.int64)
        _, unique_idx = np.unique(coords, axis=0, return_index=True)
        return points[np.sort(unique_idx)]
