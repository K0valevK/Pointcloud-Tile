"""Базовые unit-тесты."""

import numpy as np
import pytest

from pointcloud_tile.models.tile import BoundingBox, TileCoord
from pointcloud_tile.preprocessing.filters import preserve_extremes, statistical_outlier_removal
from pointcloud_tile.preprocessing.normalizer import normalize_coordinates
from pointcloud_tile.tiling.index import QuadTreeIndex
from pointcloud_tile.tiling.lod import LoDGenerator
from pointcloud_tile.storage.encoder import encode_points_binary


def test_tile_coord_path():
    coord = TileCoord(z=2, x=1, y=3, lod=2)
    assert coord.path_segment() == "2/1/3/lod2"


def test_normalize_coordinates():
    points = np.array([[10.0, 20.0, 5.0], [11.0, 21.0, 6.0]])
    normalized, origin = normalize_coordinates(points)
    assert origin == (10.0, 20.0, 5.0)
    assert normalized[0, 0] == pytest.approx(0.0)


def test_statistical_outlier_removal():
    rng = np.random.default_rng(42)
    core = rng.normal(size=(100, 3))
    outliers = np.array([[100.0, 100.0, 100.0], [-100.0, -100.0, -100.0]])
    points = np.vstack([core, outliers])
    filtered = statistical_outlier_removal(points, nb_neighbors=10, std_ratio=1.5)
    assert len(filtered) < len(points)


def test_preserve_extremes():
    points = np.array([[0, 0, 0], [1, 1, 1], [2, 2, 100], [3, 3, -50]], dtype=float)
    sampled = np.array([[1, 1, 1]], dtype=float)
    result = preserve_extremes(points, sampled)
    assert len(result) >= 2


def test_quadtree_build_and_query():
    rng = np.random.default_rng(0)
    points = rng.uniform(0, 100, size=(500, 3))
    index = QuadTreeIndex(max_depth=4, max_points_per_node=100)
    bbox = BoundingBox(0, 0, 100, 100)
    root = index.build(points, bbox)
    tiles = index.iter_tiles(root)
    assert len(tiles) > 0
    coord = tiles[0]
    indices = index.query_tile(root, coord)
    assert len(indices) >= 0


def test_lod_generator_levels():
    rng = np.random.default_rng(1)
    points = rng.uniform(0, 50, size=(1000, 3))
    gen = LoDGenerator(num_levels=5)
    levels = gen.generate(points)
    assert set(levels.keys()) == {0, 1, 2, 3, 4}
    assert len(levels[0]) == len(points)
    assert len(levels[4]) <= len(levels[0])


def test_encode_points_binary():
    points = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=float)
    data = encode_points_binary(points)
    assert len(data) > 0
