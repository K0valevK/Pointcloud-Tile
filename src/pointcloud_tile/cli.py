"""CLI-утилита для тайлирования облаков точек."""

import json
from pathlib import Path

import click
import uvicorn

from pointcloud_tile.config import Settings, get_settings
from pointcloud_tile.preprocessing import PreprocessPipeline
from pointcloud_tile.storage import create_storage
from pointcloud_tile.tiling import TilingPipeline


@click.group()
@click.version_option(package_name="pointcloud-tile")
def main() -> None:
    """Pointcloud-Tile — тайлирование и раздача облаков точек."""


@main.command("serve")
@click.option("--host", default=None, help="HTTP host")
@click.option("--port", default=None, type=int, help="HTTP port")
@click.option("--reload", is_flag=True, help="Auto-reload (dev)")
def serve(host: str | None, port: int | None, reload: bool) -> None:
    """Запуск HTTP-сервера TMS/WMTS."""
    settings = get_settings()
    uvicorn.run(
        "pointcloud_tile.api.app:create_app",
        factory=True,
        host=host or settings.host,
        port=port or settings.port,
        reload=reload,
    )


@main.command("tile")
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.option("--layer", required=True, help="Имя слоя")
@click.option("--no-outliers", is_flag=True, help="Отключить фильтрацию выбросов")
@click.option("--resume/--no-resume", default=True, help="Возобновить с чекпоинта")
def tile(input_path: Path, layer: str, no_outliers: bool, resume: bool) -> None:
    """Предобработка и тайлирование входного файла."""
    settings = get_settings()
    settings.tiles_dir.mkdir(parents=True, exist_ok=True)
    settings.layers_dir.mkdir(parents=True, exist_ok=True)
    settings.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    click.echo(f"Preprocessing {input_path}...")
    pipeline = PreprocessPipeline(remove_outliers=not no_outliers)
    points, meta = pipeline.run(input_path)

    click.echo(f"Processed {meta.get('processed_point_count', 0)} points. Tiling...")
    storage = create_storage(settings)
    tiling = TilingPipeline(settings, storage)
    result = tiling.tile_layer(layer, points, resume=resume)

    layer_meta = {
        "name": layer,
        "title": layer,
        "abstract": f"Tiled from {input_path.name}",
        "bbox": [
            meta["bbox"]["min_x"],
            meta["bbox"]["min_y"],
            meta["bbox"]["max_x"],
            meta["bbox"]["max_y"],
        ],
        "crs": meta.get("crs", "EPSG:4326"),
        "lod_levels": list(range(settings.lod_levels)),
        "point_count": meta.get("processed_point_count", 0),
        "tile_formats": ["laz", "bin"],
    }
    meta_path = settings.layers_dir / f"{layer}.json"
    meta_path.write_text(json.dumps(layer_meta, indent=2), encoding="utf-8")

    click.echo(f"Done: {result}")


@main.command("cache-invalidate")
@click.option("--layer", required=True, help="Имя слоя для инвалидации кэша")
def cache_invalidate(layer: str) -> None:
    """Инвалидация кэша Redis для слоя."""
    from pointcloud_tile.cache import TileCache

    settings = get_settings()
    cache = TileCache(settings)
    deleted = cache.invalidate_layer(layer)
    click.echo(f"Invalidated {deleted} cache keys for layer '{layer}'")


if __name__ == "__main__":
    main()
