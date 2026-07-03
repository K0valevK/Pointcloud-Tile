"""Locust-сценарии нагрузочного тестирования."""

from locust import HttpUser, between, task


class TileServiceUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(3)
    def get_tms_tile(self):
        self.client.get("/tms/1.0.0/demo/0/0/0.laz", name="/tms/[version]/[layer]/[z]/[x]/[y].laz")

    @task(1)
    def get_wmts_capabilities(self):
        self.client.get("/wmts?SERVICE=WMTS&REQUEST=GetCapabilities", name="/wmts GetCapabilities")

    @task(1)
    def list_layers(self):
        self.client.get("/layers", name="/layers")
