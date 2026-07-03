"""Конфигурация приложения."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки сервиса (переменные окружения или .env)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Общие
    app_name: str = "Pointcloud-Tile"
    debug: bool = False
    log_level: str = "INFO"

    # HTTP API
    host: str = "0.0.0.0"
    port: int = 8000
    tms_version: str = "1.0.0"
    default_tile_format: Literal["laz", "bin"] = "laz"

    # Тайлирование
    tile_size_m: float = 100.0
    lod_levels: int = Field(default=5, ge=1, le=10)
    max_tile_size_mb: float = 5.0
    points_per_minute_target: int = 10_000_000

    # Хранилище
    storage_backend: Literal["filesystem", "s3"] = "filesystem"
    tiles_dir: Path = Path("/data/tiles")
    layers_dir: Path = Path("/data/layers")

    # S3 / MinIO
    s3_endpoint_url: str | None = "http://minio:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "pointcloud-tiles"
    s3_region: str = "us-east-1"

    # Redis
    redis_url: str = "redis://redis:6379/0"
    cache_ttl_seconds: int = 3600
    cache_enabled: bool = True

    # Чекпоинты тайлирования
    checkpoint_dir: Path = Path("/data/checkpoints")


def get_settings() -> Settings:
    return Settings()
