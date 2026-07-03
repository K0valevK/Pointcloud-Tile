"""Тесты HTTP API."""

import pytest
from fastapi.testclient import TestClient

from pointcloud_tile.api.app import create_app
from pointcloud_tile.config import Settings


@pytest.fixture
def client(tmp_path):
    settings = Settings(
        tiles_dir=tmp_path / "tiles",
        layers_dir=tmp_path / "layers",
        checkpoint_dir=tmp_path / "checkpoints",
        cache_enabled=False,
    )
    settings.tiles_dir.mkdir(parents=True)
    settings.layers_dir.mkdir(parents=True)
    app = create_app(settings)
    with TestClient(app) as c:
        yield c


def test_list_layers_empty(client):
    response = client.get("/layers")
    assert response.status_code == 200
    assert response.json() == []


def test_wmts_get_capabilities(client):
    response = client.get("/wmts?SERVICE=WMTS&REQUEST=GetCapabilities")
    assert response.status_code == 200
    assert "Capabilities" in response.text
    assert "pointcloud" in response.text


def test_tms_tile_not_found(client):
    response = client.get("/tms/1.0.0/demo/0/0/0.laz")
    assert response.status_code == 404
