"""Фабрики Reader/Writer с автоматическим определением формата."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from pointcloud_tile.preprocessing.exceptions import UnsupportedFormatError
from pointcloud_tile.preprocessing.io.base import BaseReader, BaseWriter
from pointcloud_tile.preprocessing.io.las_reader import LASReader
from pointcloud_tile.preprocessing.io.laz_reader import LAZReader
from pointcloud_tile.preprocessing.io.las_writer import LASWriter
from pointcloud_tile.preprocessing.io.laz_writer import LAZWriter
from pointcloud_tile.preprocessing.io.ply_reader import PLYReader
from pointcloud_tile.preprocessing.io.ply_writer import PLYWriter
from pointcloud_tile.preprocessing.models.enums import PointCloudFormat
from pointcloud_tile.preprocessing.utils.format_detection import detect_format

ReaderT = TypeVar("ReaderT", bound=BaseReader)
WriterT = TypeVar("WriterT", bound=BaseWriter)

READER_REGISTRY: dict[PointCloudFormat, type[BaseReader]] = {
    PointCloudFormat.LAS: LASReader,
    PointCloudFormat.LAZ: LAZReader,
    PointCloudFormat.PLY: PLYReader,
}

WRITER_REGISTRY: dict[PointCloudFormat, type[BaseWriter]] = {
    PointCloudFormat.LAS: LASWriter,
    PointCloudFormat.LAZ: LAZWriter,
    PointCloudFormat.PLY: PLYWriter,
}


def create_reader(path: Path | str, *, fmt: PointCloudFormat | None = None) -> BaseReader:
    """Создаёт Reader для файла; формат определяется автоматически, если не задан."""
    file_path = Path(path)
    point_format = fmt or detect_format(file_path)
    reader_cls = READER_REGISTRY.get(point_format)
    if reader_cls is None:
        raise UnsupportedFormatError(file_path, f"No reader for format {point_format}")
    return reader_cls(file_path)


def create_writer(
    path: Path | str,
    *,
    fmt: PointCloudFormat | None = None,
) -> BaseWriter:
    """Создаёт Writer для файла; формат определяется по расширению или явно."""
    file_path = Path(path)
    point_format = fmt or detect_format_from_path_or_raise(file_path)
    writer_cls = WRITER_REGISTRY.get(point_format)
    if writer_cls is None:
        raise UnsupportedFormatError(file_path, f"No writer for format {point_format}")
    return writer_cls(file_path)


def detect_format_from_path_or_raise(path: Path) -> PointCloudFormat:
    fmt = PointCloudFormat.from_extension(path.suffix)
    if fmt is None:
        raise UnsupportedFormatError(path, "Cannot infer writer format from extension")
    return fmt


def get_reader_for_format(fmt: PointCloudFormat) -> type[BaseReader]:
    reader_cls = READER_REGISTRY.get(fmt)
    if reader_cls is None:
        raise UnsupportedFormatError(".", f"No reader registered for {fmt}")
    return reader_cls


def get_writer_for_format(fmt: PointCloudFormat) -> type[BaseWriter]:
    writer_cls = WRITER_REGISTRY.get(fmt)
    if writer_cls is None:
        raise UnsupportedFormatError(".", f"No writer registered for {fmt}")
    return writer_cls
