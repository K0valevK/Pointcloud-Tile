"""Запись PLY-файлов."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from pointcloud_tile.preprocessing.exceptions import WriterError
from pointcloud_tile.preprocessing.io.base import BaseWriter
from pointcloud_tile.preprocessing.models.enums import PointCloudFormat
from pointcloud_tile.preprocessing.models.point_cloud import PointCloud


class PLYWriter(BaseWriter):
    """Запись PLY через Open3D."""

    format = PointCloudFormat.PLY

    def __init__(self, path: Path | str, *, ascii_format: bool = False) -> None:
        super().__init__(path)
        if self.path.suffix.lower() != ".ply":
            self.path = self.path.with_suffix(".ply")
        self.ascii_format = ascii_format

    def write(self, point_cloud: PointCloud) -> Path:
        try:
            import open3d as o3d

            self.path.parent.mkdir(parents=True, exist_ok=True)
            o3d_cloud = o3d.geometry.PointCloud()
            o3d_cloud.points = o3d.utility.Vector3dVector(point_cloud.xyz)

            if point_cloud.has_rgb:
                colors = np.column_stack(
                    [
                        point_cloud.red.astype(np.float64) / 255.0,
                        point_cloud.green.astype(np.float64) / 255.0,
                        point_cloud.blue.astype(np.float64) / 255.0,
                    ]
                )
                o3d_cloud.colors = o3d.utility.Vector3dVector(colors)

            written = o3d.io.write_point_cloud(
                str(self.path),
                o3d_cloud,
                write_ascii=self.ascii_format,
            )
            if not written:
                raise WriterError(self.path, "Open3D write_point_cloud returned False")
            return self.path
        except WriterError:
            raise
        except Exception as exc:
            raise WriterError(self.path, "PLY write failed", cause=exc) from exc
