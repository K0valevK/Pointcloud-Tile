"""Фабрика хранилищ тайлов."""

from pointcloud_tile.config import Settings
from pointcloud_tile.storage.base import TileStorage
from pointcloud_tile.storage.filesystem import FilesystemTileStorage
from pointcloud_tile.storage.s3 import S3TileStorage


def create_storage(settings: Settings) -> TileStorage:
    if settings.storage_backend == "s3":
        return S3TileStorage(settings)
    return FilesystemTileStorage(settings.tiles_dir)
