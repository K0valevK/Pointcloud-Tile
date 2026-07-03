"""Кодирование точек в LAZ и бинарный потоковый формат."""

import io

import numpy as np


def encode_points_laz(points: np.ndarray) -> bytes:
    """Сериализует точки в LAZ (минимальный LAS 1.4 point record)."""
    import laspy

    header = laspy.LasHeader(point_format=0, version="1.4")
    header.offsets = [
        float(points[:, 0].min()) if len(points) else 0.0,
        float(points[:, 1].min()) if len(points) else 0.0,
        float(points[:, 2].min()) if len(points) else 0.0,
    ]
    las = laspy.LasData(header)
    if len(points):
        las.x = points[:, 0]
        las.y = points[:, 1]
        las.z = points[:, 2]
    buffer = io.BytesIO()
    las.write(buffer)
    return buffer.getvalue()


def encode_points_binary(points: np.ndarray) -> bytes:
    """Специализированный бинарный формат: [count:uint32][x,y,z:float32 × N]."""
    count = np.array([len(points)], dtype=np.uint32)
    if len(points) == 0:
        return count.tobytes()
    coords = points[:, :3].astype(np.float32)
    return count.tobytes() + coords.tobytes()
