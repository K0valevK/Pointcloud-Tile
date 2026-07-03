"""Пространственная нормализация координат."""

import numpy as np


def normalize_coordinates(
    points: np.ndarray,
    origin: tuple[float, float, float] | None = None,
) -> tuple[np.ndarray, tuple[float, float, float]]:
    """Смещает облако точек так, чтобы origin стал (0, 0, 0) или заданной точкой."""
    if origin is None:
        origin = (float(points[:, 0].min()), float(points[:, 1].min()), float(points[:, 2].min()))

    offset = np.array(origin, dtype=np.float64)
    normalized = points.astype(np.float64, copy=True)
    normalized[:, :3] -= offset
    return normalized, origin
