"""Фильтрация выбросов и семантически важных точек."""

import numpy as np
from scipy.spatial import cKDTree


def statistical_outlier_removal(
    points: np.ndarray,
    nb_neighbors: int = 20,
    std_ratio: float = 2.0,
) -> np.ndarray:
    """Удаляет статистические выбросы на основе среднего расстояния до соседей."""
    if len(points) <= nb_neighbors:
        return points

    tree = cKDTree(points[:, :3])
    distances, _ = tree.query(points[:, :3], k=nb_neighbors + 1)
    mean_dist = distances[:, 1:].mean(axis=1)
    threshold = mean_dist.mean() + std_ratio * mean_dist.std()
    mask = mean_dist <= threshold
    return points[mask]


def preserve_extremes(
    points: np.ndarray,
    sampled: np.ndarray,
    z_percentile: float = 0.01,
) -> np.ndarray:
    """Добавляет к прореженному облаку точки с экстремальными высотами."""
    if len(points) == 0 or len(sampled) == 0:
        return sampled

    z = points[:, 2]
    low = np.percentile(z, z_percentile * 100)
    high = np.percentile(z, (1 - z_percentile) * 100)
    extremes = points[(z <= low) | (z >= high)]
    if len(extremes) == 0:
        return sampled

    combined = np.vstack([sampled, extremes])
    _, unique_idx = np.unique(combined[:, :3], axis=0, return_index=True)
    return combined[np.sort(unique_idx)]
