"""Метаданные слоёв."""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from pointcloud_tile.api.schemas import LayerInfoResponse

router = APIRouter(prefix="/layers")


@router.get("", response_model=list[str])
async def list_layers(request: Request) -> list[str]:
    """Список доступных слоёв."""
    settings = request.app.state.settings
    layers_dir = settings.layers_dir
    if not layers_dir.exists():
        return []
    return sorted(p.stem for p in layers_dir.glob("*.json"))


@router.get("/{layer_name}", response_model=LayerInfoResponse)
async def get_layer_metadata(request: Request, layer_name: str) -> LayerInfoResponse:
    """Метаданные слоя: охват, CRS, LoD, число точек."""
    settings = request.app.state.settings
    meta_path = settings.layers_dir / f"{layer_name}.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail=f"Layer not found: {layer_name}")

    data = json.loads(meta_path.read_text(encoding="utf-8"))
    return LayerInfoResponse(**data)
