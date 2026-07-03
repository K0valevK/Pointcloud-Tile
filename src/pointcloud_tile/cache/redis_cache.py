"""Кэширование тайлов в Redis."""

import hashlib

import redis

from pointcloud_tile.config import Settings
from pointcloud_tile.models.tile import TileCoord, TileFilter


class TileCache:
    """Кэш тайлов с TTL и инвалидацией по слою."""

    def __init__(self, settings: Settings) -> None:
        self.enabled = settings.cache_enabled
        self.ttl = settings.cache_ttl_seconds
        self._client: redis.Redis | None = None
        if self.enabled:
            self._client = redis.from_url(settings.redis_url, decode_responses=False)

    def _key(
        self,
        layer: str,
        coord: TileCoord,
        tile_format: str,
        filters: TileFilter | None = None,
    ) -> str:
        filter_hash = ""
        if filters:
            raw = f"{filters.intensity_min}:{filters.intensity_max}:{filters.classification}"
            filter_hash = hashlib.md5(raw.encode()).hexdigest()[:8]
        return f"tile:{layer}:{coord.path_segment()}:{tile_format}:{filter_hash}"

    def get(
        self,
        layer: str,
        coord: TileCoord,
        tile_format: str,
        filters: TileFilter | None = None,
    ) -> bytes | None:
        if not self._client:
            return None
        data = self._client.get(self._key(layer, coord, tile_format, filters))
        return bytes(data) if data else None

    def set(
        self,
        layer: str,
        coord: TileCoord,
        tile_format: str,
        data: bytes,
        filters: TileFilter | None = None,
    ) -> None:
        if not self._client:
            return
        self._client.setex(self._key(layer, coord, tile_format, filters), self.ttl, data)

    def invalidate_layer(self, layer: str) -> int:
        """Удаляет все ключи кэша для слоя."""
        if not self._client:
            return 0
        pattern = f"tile:{layer}:*"
        deleted = 0
        for key in self._client.scan_iter(match=pattern, count=500):
            self._client.delete(key)
            deleted += 1
        return deleted
