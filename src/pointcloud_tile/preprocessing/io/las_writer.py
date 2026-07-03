"""Общая логика записи LAS/LAZ через laspy."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from pointcloud_tile.preprocessing.exceptions import WriterError
from pointcloud_tile.preprocessing.io.base import BaseWriter
from pointcloud_tile.preprocessing.models.enums import PointCloudFormat
from pointcloud_tile.preprocessing.models.point_cloud import PointCloud


class _LasFamilyWriter(BaseWriter):
    """Базовая реализация записи LAS/LAZ."""

    format: PointCloudFormat
    compressed: bool

    def write(self, point_cloud: PointCloud) -> Path:
        try:
            import laspy

            self.path.parent.mkdir(parents=True, exist_ok=True)
            header = laspy.LasHeader(point_format=self._select_point_format(point_cloud), version="1.4")
            if point_cloud.point_count > 0:
                header.offsets = [
                    float(point_cloud.xyz[:, 0].min()),
                    float(point_cloud.xyz[:, 1].min()),
                    float(point_cloud.xyz[:, 2].min()),
                ]

            las = laspy.LasData(header)
            if point_cloud.point_count > 0:
                las.x = point_cloud.xyz[:, 0]
                las.y = point_cloud.xyz[:, 1]
                las.z = point_cloud.xyz[:, 2]
                if point_cloud.intensity is not None:
                    las.intensity = point_cloud.intensity
                if point_cloud.classification is not None:
                    las.classification = point_cloud.classification
                if point_cloud.has_rgb:
                    las.red = point_cloud.red
                    las.green = point_cloud.green
                    las.blue = point_cloud.blue

            las.write(str(self.path), do_compress=self.compressed)
            return self.path
        except Exception as exc:
            raise WriterError(self.path, "LAS/LAZ write failed", cause=exc) from exc

    @staticmethod
    def _select_point_format(point_cloud: PointCloud) -> int:
        if point_cloud.has_rgb:
            return 2
        if point_cloud.classification is not None or point_cloud.intensity is not None:
            return 1
        return 0


class LASWriter(_LasFamilyWriter):
    """Запись несжатых LAS-файлов."""

    format = PointCloudFormat.LAS
    compressed = False

    def __init__(self, path: Path | str) -> None:
        super().__init__(path)
        if self.path.suffix.lower() != ".las":
            self.path = self.path.with_suffix(".las")


class LAZWriter(_LasFamilyWriter):
    """Запись сжатых LAZ-файлов."""

    format = PointCloudFormat.LAZ
    compressed = True

    def __init__(self, path: Path | str) -> None:
        super().__init__(path)
        if self.path.suffix.lower() != ".laz":
            self.path = self.path.with_suffix(".laz")
