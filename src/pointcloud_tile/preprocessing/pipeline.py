"""Конвейер предобработки: чтение → нормализация → фильтрация."""

from pathlib import Path
from typing import Any

import numpy as np

from pointcloud_tile.preprocessing.filters import statistical_outlier_removal
from pointcloud_tile.preprocessing.io.factory import create_reader
from pointcloud_tile.preprocessing.models.metadata import PointCloudHeader
from pointcloud_tile.preprocessing.models.point_cloud import PointCloud
from pointcloud_tile.preprocessing.normalizer import normalize_coordinates


class PreprocessPipeline:
    """Предобработка входного облака точек перед тайлированием."""

    def __init__(
        self,
        remove_outliers: bool = True,
        nb_neighbors: int = 20,
        std_ratio: float = 2.0,
    ) -> None:
        self.remove_outliers = remove_outliers
        self.nb_neighbors = nb_neighbors
        self.std_ratio = std_ratio

    def run(self, input_path: Path) -> tuple[np.ndarray, dict[str, Any]]:
        """Обрабатывает файл и возвращает точки (N×3) и метаданные."""
        point_cloud, meta = self.run_point_cloud(input_path)
        return point_cloud.to_xyz_array(), meta

    def run_point_cloud(self, input_path: Path) -> tuple[PointCloud, dict[str, Any]]:
        """Обрабатывает файл и возвращает типизированный PointCloud."""
        reader = create_reader(input_path)
        header: PointCloudHeader = reader.read_header()
        chunks: list[np.ndarray] = []

        for chunk in reader.iter_chunks():
            xyz = chunk.to_xyz_array()
            if self.remove_outliers and len(xyz) > 0:
                xyz = statistical_outlier_removal(
                    xyz,
                    nb_neighbors=self.nb_neighbors,
                    std_ratio=self.std_ratio,
                )
            if len(xyz) > 0:
                chunks.append(xyz)

        meta: dict[str, Any] = {
            "point_count": header.point_count,
            "crs": header.crs or "unknown",
            "format": header.format.value,
            "bbox": {
                "min_x": header.bbox.min_x if header.bbox else 0.0,
                "min_y": header.bbox.min_y if header.bbox else 0.0,
                "max_x": header.bbox.max_x if header.bbox else 0.0,
                "max_y": header.bbox.max_y if header.bbox else 0.0,
                "min_z": header.bbox.min_z if header.bbox else 0.0,
                "max_z": header.bbox.max_z if header.bbox else 0.0,
            },
        }

        if not chunks:
            empty = PointCloud.empty().with_metadata(
                source_path=str(input_path),
                source_format=header.format,
                crs=header.crs,
                processed_point_count=0,
            )
            meta["processed_point_count"] = 0
            return empty, meta

        xyz = np.vstack(chunks)
        xyz, origin = normalize_coordinates(xyz)
        meta["origin"] = origin
        meta["processed_point_count"] = len(xyz)

        cloud = PointCloud.from_xyz(
            xyz,
            source_format=header.format,
            source_path=str(input_path),
        ).with_metadata(
            crs=header.crs,
            origin=origin,
            processed_point_count=len(xyz),
        )
        return cloud, meta
