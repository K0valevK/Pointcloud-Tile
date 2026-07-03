"""Типизированная модель облака точек."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Self

import numpy as np
import numpy.typing as npt

from pointcloud_tile.preprocessing.exceptions import InvalidPointCloudError
from pointcloud_tile.preprocessing.models.metadata import AxisAlignedBoundingBox, PointCloudMetadata

if TYPE_CHECKING:
    from pointcloud_tile.preprocessing.models.enums import PointCloudFormat


@dataclass(slots=True)
class PointCloud:
    """
    Облако точек с координатами и опциональными атрибутами LAS/PLY.

    Все массивы атрибутов имеют длину ``point_count`` и выровнены по индексу точки.
    """

    xyz: npt.NDArray[np.float64]
    intensity: npt.NDArray[np.float32] | None = None
    classification: npt.NDArray[np.uint8] | None = None
    red: npt.NDArray[np.uint8] | None = None
    green: npt.NDArray[np.uint8] | None = None
    blue: npt.NDArray[np.uint8] | None = None
    return_number: npt.NDArray[np.uint8] | None = None
    number_of_returns: npt.NDArray[np.uint8] | None = None
    metadata: PointCloudMetadata = field(default_factory=PointCloudMetadata)

    def __post_init__(self) -> None:
        self.validate()

    @property
    def point_count(self) -> int:
        return int(self.xyz.shape[0])

    @property
    def has_rgb(self) -> bool:
        return self.red is not None and self.green is not None and self.blue is not None

    @property
    def bbox(self) -> AxisAlignedBoundingBox:
        if self.point_count == 0:
            return AxisAlignedBoundingBox(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        return AxisAlignedBoundingBox.from_arrays(self.xyz[:, 0], self.xyz[:, 1], self.xyz[:, 2])

    def validate(self) -> None:
        if self.xyz.ndim != 2 or self.xyz.shape[1] != 3:
            raise InvalidPointCloudError("xyz must have shape (N, 3)")

        n = self.point_count
        for name, array in (
            ("intensity", self.intensity),
            ("classification", self.classification),
            ("red", self.red),
            ("green", self.green),
            ("blue", self.blue),
            ("return_number", self.return_number),
            ("number_of_returns", self.number_of_returns),
        ):
            if array is not None and len(array) != n:
                raise InvalidPointCloudError(
                    f"Attribute '{name}' length {len(array)} does not match point count {n}"
                )

    def with_metadata(
        self,
        *,
        source_path: str | None = None,
        source_format: PointCloudFormat | None = None,
        crs: str | None = None,
        origin: tuple[float, float, float] | None = None,
        processed_point_count: int | None = None,
        extra: dict[str, object] | None = None,
    ) -> Self:
        """Возвращает копию с обновлёнными полями metadata."""
        meta = PointCloudMetadata(
            source_path=source_path if source_path is not None else self.metadata.source_path,
            source_format=(
                source_format if source_format is not None else self.metadata.source_format
            ),
            crs=crs if crs is not None else self.metadata.crs,
            origin=origin if origin is not None else self.metadata.origin,
            processed_point_count=(
                processed_point_count
                if processed_point_count is not None
                else self.metadata.processed_point_count
            ),
            extra=extra if extra is not None else self.metadata.extra.copy(),
        )
        return self.__class__(
            xyz=self.xyz,
            intensity=self.intensity,
            classification=self.classification,
            red=self.red,
            green=self.green,
            blue=self.blue,
            return_number=self.return_number,
            number_of_returns=self.number_of_returns,
            metadata=meta,
        )

    def to_xyz_array(self) -> npt.NDArray[np.float64]:
        """Координаты N×3 (удобно для legacy-кода тайлирования)."""
        return self.xyz

    @classmethod
    def from_xyz(
        cls,
        xyz: npt.NDArray[np.float64],
        *,
        source_format: PointCloudFormat | None = None,
        source_path: str | None = None,
    ) -> Self:
        coords = np.asarray(xyz, dtype=np.float64)
        if coords.ndim != 2 or coords.shape[1] != 3:
            raise InvalidPointCloudError("xyz must have shape (N, 3)")
        return cls(
            xyz=coords,
            metadata=PointCloudMetadata(
                source_path=source_path,
                source_format=source_format,
            ),
        )

    @classmethod
    def empty(cls) -> Self:
        return cls(xyz=np.empty((0, 3), dtype=np.float64))
