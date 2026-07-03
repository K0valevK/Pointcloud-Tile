"""Пространственное индексирование (квадродерево)."""

from dataclasses import dataclass, field

import numpy as np
from shapely.geometry import box

from pointcloud_tile.models.tile import BoundingBox, TileCoord


@dataclass
class QuadTreeNode:
    """Узел квадродерева с привязанными индексами точек."""

    bbox: BoundingBox
    depth: int
    point_indices: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.int64))
    children: list["QuadTreeNode"] | None = None

    @property
    def is_leaf(self) -> bool:
        return self.children is None


class QuadTreeIndex:
    """Квадродерево для пространственной нарезки облака точек на тайлы."""

    def __init__(self, max_depth: int = 10, max_points_per_node: int = 50_000) -> None:
        self.max_depth = max_depth
        self.max_points_per_node = max_points_per_node

    def build(self, points: np.ndarray, root_bbox: BoundingBox | None = None) -> QuadTreeNode:
        """Строит индекс по массиву точек."""
        if root_bbox is None:
            root_bbox = BoundingBox(
                min_x=float(points[:, 0].min()),
                min_y=float(points[:, 1].min()),
                max_x=float(points[:, 0].max()),
                max_y=float(points[:, 1].max()),
            )

        indices = np.arange(len(points), dtype=np.int64)
        return self._split(points, root_bbox, depth=0, indices=indices)

    def query_tile(self, root: QuadTreeNode, coord: TileCoord) -> np.ndarray:
        """Возвращает индексы точек для тайла (z, x, y)."""
        node = self._find_node(root, coord.z, coord.x, coord.y)
        return node.point_indices if node else np.array([], dtype=np.int64)

    def iter_tiles(self, root: QuadTreeNode) -> list[TileCoord]:
        """Обходит дерево и возвращает координаты всех листовых тайлов."""
        coords: list[TileCoord] = []
        self._collect_leaves(root, coords, x=0, y=0, z=0)
        return coords

    def _split(
        self,
        points: np.ndarray,
        bbox: BoundingBox,
        depth: int,
        indices: np.ndarray,
    ) -> QuadTreeNode:
        node = QuadTreeNode(bbox=bbox, depth=depth, point_indices=indices)

        if depth >= self.max_depth or len(indices) <= self.max_points_per_node:
            return node

        mid_x = (bbox.min_x + bbox.max_x) / 2
        mid_y = (bbox.min_y + bbox.max_y) / 2
        px = points[indices, 0]
        py = points[indices, 1]

        quadrants = [
            (BoundingBox(bbox.min_x, bbox.min_y, mid_x, mid_y), (px <= mid_x) & (py <= mid_y)),
            (BoundingBox(mid_x, bbox.min_y, bbox.max_x, mid_y), (px > mid_x) & (py <= mid_y)),
            (BoundingBox(bbox.min_x, mid_y, mid_x, bbox.max_y), (px <= mid_x) & (py > mid_y)),
            (BoundingBox(mid_x, mid_y, bbox.max_x, bbox.max_y), (px > mid_x) & (py > mid_y)),
        ]

        children: list[QuadTreeNode] = []
        for child_bbox, mask in quadrants:
            child_indices = indices[mask]
            if len(child_indices) == 0:
                continue
            children.append(self._split(points, child_bbox, depth + 1, child_indices))

        if children:
            node.children = children
            node.point_indices = np.array([], dtype=np.int64)
        return node

    def _find_node(
        self,
        node: QuadTreeNode,
        z: int,
        x: int,
        y: int,
        depth: int = 0,
        cur_x: int = 0,
        cur_y: int = 0,
    ) -> QuadTreeNode | None:
        if depth == z:
            return node if cur_x == x and cur_y == y else None

        if node.is_leaf or not node.children:
            return None

        mid_bit = 1 << (z - depth - 1)
        for i, child in enumerate(node.children):
            cx = cur_x + (i % 2) * mid_bit
            cy = cur_y + (i // 2) * mid_bit
            found = self._find_node(child, z, x, y, depth + 1, cx, cy)
            if found:
                return found
        return None

    def _collect_leaves(
        self,
        node: QuadTreeNode,
        coords: list[TileCoord],
        x: int,
        y: int,
        z: int,
    ) -> None:
        if node.is_leaf or not node.children:
            coords.append(TileCoord(z=z, x=x, y=y))
            return

        for i, child in enumerate(node.children):
            self._collect_leaves(child, coords, x * 2 + i % 2, y * 2 + i // 2, z + 1)

    @staticmethod
    def tile_polygon(bbox: BoundingBox):
        """Возвращает Shapely-полигон тайла."""
        return box(bbox.min_x, bbox.min_y, bbox.max_x, bbox.max_y)
