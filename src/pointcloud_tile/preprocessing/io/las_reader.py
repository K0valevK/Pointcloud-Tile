"""Общая логика чтения LAS/LAZ через laspy."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np

from pointcloud_tile.preprocessing.exceptions import ReaderError
from pointcloud_tile.preprocessing.io.base import BaseReader
from pointcloud_tile.preprocessing.models.enums import PointCloudFormat
from pointcloud_tile.preprocessing.models.metadata import AxisAlignedBoundingBox, PointCloudHeader
from pointcloud_tile.preprocessing.models.point_cloud import PointCloud


class _LasFamilyReader(BaseReader):
    """Базовая реализация для LAS и LAZ (laspy)."""

    format: PointCloudFormat

    def read_header(self) -> PointCloudHeader:
        try:
            import laspy

            with laspy.open(self.path) as reader:
                header = reader.header
                bbox = AxisAlignedBoundingBox(
                    min_x=float(header.x_min),
                    min_y=float(header.y_min),
                    min_z=float(header.z_min),
                    max_x=float(header.x_max),
                    max_y=float(header.y_max),
                    max_z=float(header.z_max),
                )
                crs = getattr(header, "crs", None)
                return PointCloudHeader(
                    point_count=int(header.point_count),
                    format=self.format,
                    crs=str(crs) if crs is not None else None,
                    bbox=bbox,
                    point_format_id=int(header.point_format.id),
                    version=f"{header.version.major}.{header.version.minor}",
                    source_path=str(self.path),
                )
        except Exception as exc:
            raise ReaderError(self.path, "LAS/LAZ header read failed", cause=exc) from exc

    def read(self) -> PointCloud:
        try:
            import laspy

            header = self.read_header()
            with laspy.open(self.path) as reader:
                points = reader.read()
                return self._points_to_cloud(points, header=header)
        except Exception as exc:
            raise ReaderError(self.path, "LAS/LAZ read failed", cause=exc) from exc

    def iter_chunks(self, chunk_size: int = 1_000_000) -> Iterator[PointCloud]:
        try:
            import laspy

            header = self.read_header()
            with laspy.open(self.path) as reader:
                for chunk in reader.chunk_iterator(chunk_size):
                    yield self._points_to_cloud(chunk, header=header)
        except Exception as exc:
            raise ReaderError(self.path, "LAS/LAZ chunk read failed", cause=exc) from exc

    def _points_to_cloud(
        self,
        points: Any,
        *,
        header: PointCloudHeader,
    ) -> PointCloud:
        xyz = np.column_stack(
            [
                np.asarray(points.x, dtype=np.float64),
                np.asarray(points.y, dtype=np.float64),
                np.asarray(points.z, dtype=np.float64),
            ]
        )

        intensity: np.ndarray | None = None
        if hasattr(points, "intensity"):
            intensity = np.asarray(points.intensity, dtype=np.float32)

        classification: np.ndarray | None = None
        if hasattr(points, "classification"):
            classification = np.asarray(points.classification, dtype=np.uint8)

        red = green = blue = None
        if hasattr(points, "red") and hasattr(points, "green") and hasattr(points, "blue"):
            red = np.asarray(points.red, dtype=np.uint8)
            green = np.asarray(points.green, dtype=np.uint8)
            blue = np.asarray(points.blue, dtype=np.uint8)

        return_num = num_returns = None
        if hasattr(points, "return_number"):
            return_num = np.asarray(points.return_number, dtype=np.uint8)
        if hasattr(points, "number_of_returns"):
            num_returns = np.asarray(points.number_of_returns, dtype=np.uint8)

        from pointcloud_tile.preprocessing.models.metadata import PointCloudMetadata

        return PointCloud(
            xyz=xyz,
            intensity=intensity,
            classification=classification,
            red=red,
            green=green,
            blue=blue,
            return_number=return_num,
            number_of_returns=num_returns,
            metadata=PointCloudMetadata(
                source_path=str(self.path),
                source_format=self.format,
                crs=header.crs,
            ),
        )


class LASReader(_LasFamilyReader):
    """Читатель несжатых LAS-файлов."""

    format = PointCloudFormat.LAS

    def __init__(self, path: Path | str) -> None:
        super().__init__(path)
        if self.path.suffix.lower() not in {".las"}:
            from pointcloud_tile.preprocessing.exceptions import UnsupportedFormatError

            raise UnsupportedFormatError(self.path, "Expected .las file")


class LAZReader(_LasFamilyReader):
    """Читатель сжатых LAZ-файлов."""

    format = PointCloudFormat.LAZ

    def __init__(self, path: Path | str) -> None:
        super().__init__(path)
        if self.path.suffix.lower() not in {".laz"}:
            from pointcloud_tile.preprocessing.exceptions import UnsupportedFormatError

            raise UnsupportedFormatError(self.path, "Expected .laz file")
