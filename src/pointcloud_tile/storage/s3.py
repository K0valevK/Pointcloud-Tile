"""S3-совместимое хранилище (MinIO)."""

import boto3
from botocore.exceptions import ClientError
import numpy as np
from botocore.client import Config

from pointcloud_tile.config import Settings
from pointcloud_tile.models.tile import TileCoord
from pointcloud_tile.storage.base import TileStorage
from pointcloud_tile.storage.encoder import encode_points_laz


class S3TileStorage(TileStorage):
    """Объектное хранилище с атомарной записью через multipart upload."""

    def __init__(self, settings: Settings) -> None:
        self.bucket = settings.s3_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(signature_version="s3v4"),
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self.client.create_bucket(Bucket=self.bucket)

    def write_tile_atomic(self, layer: str, coord: TileCoord, points: np.ndarray) -> str:
        key = self.tile_key(layer, coord)
        data = encode_points_laz(points)
        tmp_key = f"{key}.tmp"

        self.client.put_object(Bucket=self.bucket, Key=tmp_key, Body=data)
        self.client.copy_object(
            Bucket=self.bucket,
            CopySource={"Bucket": self.bucket, "Key": tmp_key},
            Key=key,
        )
        self.client.delete_object(Bucket=self.bucket, Key=tmp_key)
        return f"s3://{self.bucket}/{key}"

    def read_tile(self, layer: str, coord: TileCoord) -> bytes:
        key = self.tile_key(layer, coord)
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    def exists(self, layer: str, coord: TileCoord) -> bool:
        key = self.tile_key(layer, coord)
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def delete_layer(self, layer: str) -> None:
        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=f"{layer}/"):
            objects = page.get("Contents", [])
            if objects:
                self.client.delete_objects(
                    Bucket=self.bucket,
                    Delete={"Objects": [{"Key": obj["Key"]} for obj in objects]},
                )
