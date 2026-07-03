"""Чтение PLY-файлов."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import numpy as np

from pointcloud_tile.preprocessing.exceptions import ReaderError, UnsupportedFormatError
from pointcloud_tile.preprocessing.io.base import BaseReader
from pointcloud_tile.preprocessing.models.enums import PointCloudFormat
from pointcloud_tile.preprocessing.models.metadata import (
    AxisAlignedBoundingBox,
    PointCloudHeader,
    PointCloudMetadata,
)
from pointcloud_tile.preprocessing.models.point_cloud import PointCloud


class PLYReader(BaseReader):
    """Читатель PLY через Open3D."""

    format = PointCloudFormat.PLY

    def __init__(self, path: Path | str) -> None:
        super().__init__(path)
        if self.path.suffix.lower() not in {".ply", ""}:
            raise UnsupportedFormatError(self.path, "Expected .ply file")

    def read_header(self) -> PointCloudHeader:
        cloud = self._load_open3d()
        n = len(cloud.points)
        if n == 0:
            bbox = AxisAlignedBoundingBox(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        else:
            pts = np.asarray(cloud.points)
            bbox = AxisAlignedBoundingBox.from_arrays(pts[:, 0], pts[:, 1], pts[:, 2])
        return PointCloudHeader(
            point_count=n,
            format=PointCloudFormat.PLY,
            crs=None,
            bbox=bbox,
            source_path=str(self.path),
        )

    def read(self) -> PointCloud:
        try:
            cloud = self._load_open3d()
            return self._open3d_to_point_cloud(cloud)
        except ReaderError:
            raise
        except Exception as exc:
            raise ReaderError(self.path, "PLY read failed", cause=exc) from exc

    def iter_chunks(self, chunk_size: int = 1_000_000) -> Iterator[PointCloud]:
        full = self.read()
        n = full.point_count
        if n == 0:
            yield full
            return

        for start in range(0, n, chunk_size):
            end = min(start + chunk_size, n)
            yield PointCloud(
                xyz=full.xyz[start:end].copy(),
                intensity=full.intensity[start:end].copy() if full.intensity is not None else None,
                classification=(
                    full.classification[start:end].copy()
                    if full.classification is not None
                    else None
                ),
                red=full.red[start:end].copy() if full.red is not None else None,
                green=full.green[start:end].copy() if full.green is not None else None,
                blue=full.blue[start:end].copy() if full.blue is not None else None,
                metadata=PointCloudMetadata(
                    source_path=str(self.path),
                    source_format=PointCloudFormat.PLY,
                ),
            )

    def _load_open3d(self):
        import open3d as o3d

        cloud = o3d.io.read_point_cloud(str(self.path))
        if cloud.is_empty() and self.path.stat().st_size > 0:
            raise ReaderError(self.path, "Open3D returned empty point cloud")
        return cloud

    def _open3d_to_point_cloud(self, cloud) -> PointCloud:
        pts = np.asarray(cloud.points, dtype=np.float64)
        if pts.size == 0:
            return PointCloud.empty().with_metadata(
                source_path=str(self.path),
                source_format=PointCloudFormat.PLY,
            )

        red = green = blue = None
        if cloud.has_colors():
            colors = np.asarray(cloud.colors)
            red = (colors[:, 0] * 255).astype(np.uint8)
            green = (colors[:, 1] * 255).astype(np.uint8)
            blue = (colors[:, 2] * 255).astype(np.uint8)

        return PointCloud(
            xyz=pts,
            red=red,
            green=green,
            blue=blue,
            metadata=PointCloudMetadata(
                source_path=str(self.path),
                source_format=PointCloudFormat.PLY,
            ),
        )
