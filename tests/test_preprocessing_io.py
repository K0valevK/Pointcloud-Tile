"""Тесты I/O предобработки."""

from pathlib import Path

import numpy as np
import pytest

from pointcloud_tile.preprocessing.exceptions import (
    InvalidPointCloudError,
    UnsupportedFormatError,
)
from pointcloud_tile.preprocessing.io import (
    LASReader,
    LAZReader,
    LASWriter,
    LAZWriter,
    PLYReader,
    PLYWriter,
    create_reader,
    create_writer,
)
from pointcloud_tile.preprocessing.models import PointCloud, PointCloudFormat
from pointcloud_tile.preprocessing.services import PointCloudUploadService
from pointcloud_tile.preprocessing.utils import detect_format, detect_format_from_path


@pytest.fixture
def sample_cloud() -> PointCloud:
    xyz = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]], dtype=np.float64)
    return PointCloud.from_xyz(xyz, source_format=PointCloudFormat.LAS)


@pytest.fixture
def las_file(tmp_path: Path, sample_cloud: PointCloud) -> Path:
    path = tmp_path / "sample.las"
    LASWriter(path).write(sample_cloud)
    return path


@pytest.fixture
def laz_file(tmp_path: Path, sample_cloud: PointCloud) -> Path:
    path = tmp_path / "sample.laz"
    LAZWriter(path).write(sample_cloud)
    return path


@pytest.fixture
def ply_file(tmp_path: Path, sample_cloud: PointCloud) -> Path:
    path = tmp_path / "sample.ply"
    PLYWriter(path, ascii_format=True).write(sample_cloud)
    return path


def test_point_cloud_validation():
    with pytest.raises(InvalidPointCloudError):
        PointCloud(xyz=np.array([[1.0, 2.0]], dtype=np.float64))

    cloud = PointCloud.from_xyz(np.zeros((2, 3)))
    with pytest.raises(InvalidPointCloudError):
        PointCloud(
            xyz=cloud.xyz,
            intensity=np.array([1.0], dtype=np.float32),
        )


def test_detect_format_from_path():
    assert detect_format_from_path("cloud.laz") == PointCloudFormat.LAZ
    assert detect_format_from_path("cloud.xyz") is None


def test_las_roundtrip(las_file: Path, sample_cloud: PointCloud):
    assert detect_format(las_file) == PointCloudFormat.LAS
    reader = LASReader(las_file)
    header = reader.read_header()
    assert header.point_count == sample_cloud.point_count
    cloud = reader.read()
    assert cloud.point_count == 3
    np.testing.assert_allclose(cloud.xyz, sample_cloud.xyz)


def test_laz_roundtrip(laz_file: Path):
    assert detect_format(laz_file) == PointCloudFormat.LAZ
    cloud = LAZReader(laz_file).read()
    assert cloud.point_count == 3


def test_ply_roundtrip(ply_file: Path):
    assert detect_format(ply_file) == PointCloudFormat.PLY
    cloud = PLYReader(ply_file).read()
    assert cloud.point_count == 3
    np.testing.assert_allclose(cloud.xyz[0], [1.0, 2.0, 3.0], rtol=1e-5)


def test_create_reader_factory(las_file: Path, laz_file: Path, ply_file: Path):
    assert isinstance(create_reader(las_file), LASReader)
    assert isinstance(create_reader(laz_file), LAZReader)
    assert isinstance(create_reader(ply_file), PLYReader)


def test_create_writer_factory(tmp_path: Path, sample_cloud: PointCloud):
    las_path = tmp_path / "out.las"
    create_writer(las_path).write(sample_cloud)
    assert las_path.exists()
    assert LASReader(las_path).read().point_count == 3


def test_las_iter_chunks(las_file: Path):
    chunks = list(LASReader(las_file).iter_chunks(chunk_size=2))
    assert len(chunks) >= 1
    total = sum(c.point_count for c in chunks)
    assert total == 3


def test_upload_service(tmp_path: Path, las_file: Path):
    service = PointCloudUploadService(tmp_path / "uploads")
    content = las_file.read_bytes()
    saved, cloud = service.save_and_load("scan.las", content)
    assert saved.exists()
    assert cloud.point_count == 3


def test_upload_rejects_unknown_format(tmp_path: Path):
    service = PointCloudUploadService(tmp_path / "uploads")
    with pytest.raises(UnsupportedFormatError):
        service.save_upload("bad.xyz", b"data")
