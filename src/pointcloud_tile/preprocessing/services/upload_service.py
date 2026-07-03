"""Сервис загрузки и первичной загрузки облаков точек."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from pointcloud_tile.preprocessing.exceptions import UploadError, UnsupportedFormatError
from pointcloud_tile.preprocessing.io.factory import create_reader
from pointcloud_tile.preprocessing.models.enums import PointCloudFormat
from pointcloud_tile.preprocessing.models.metadata import PointCloudHeader
from pointcloud_tile.preprocessing.models.point_cloud import PointCloud
from pointcloud_tile.preprocessing.utils.format_detection import detect_format

_SAFE_NAME = re.compile(r"[^a-zA-Z0-9._-]+")


class PointCloudUploadService:
    """Сохраняет загруженные файлы и загружает их как PointCloud."""

    def __init__(
        self,
        upload_dir: Path | str,
        *,
        allowed_formats: frozenset[PointCloudFormat] | None = None,
        max_file_size_bytes: int | None = None,
    ) -> None:
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.allowed_formats = allowed_formats or frozenset(PointCloudFormat)
        self.max_file_size_bytes = max_file_size_bytes

    def save_upload(self, filename: str, content: bytes) -> Path:
        """Сохраняет байты загруженного файла на диск с безопасным именем."""
        if not filename:
            raise UploadError("Filename is required")

        if self.max_file_size_bytes is not None and len(content) > self.max_file_size_bytes:
            raise UploadError(
                f"File exceeds maximum size of {self.max_file_size_bytes} bytes",
                filename=filename,
            )

        safe_name = _SAFE_NAME.sub("_", Path(filename).name).strip("._")
        if not safe_name:
            raise UploadError("Invalid filename", filename=filename)

        suffix = Path(safe_name).suffix.lower()
        fmt = PointCloudFormat.from_extension(suffix)
        if fmt is None:
            raise UnsupportedFormatError(safe_name, "Unknown file extension")
        if fmt not in self.allowed_formats:
            raise UnsupportedFormatError(safe_name, f"Format {fmt.value} is not allowed")

        dest = self.upload_dir / f"{uuid.uuid4().hex}_{safe_name}"
        dest.write_bytes(content)

        try:
            detected = detect_format(dest)
        except Exception as exc:
            dest.unlink(missing_ok=True)
            raise UploadError(
                f"Uploaded file failed format validation: {exc}",
                filename=filename,
            ) from exc

        if detected not in self.allowed_formats:
            dest.unlink(missing_ok=True)
            raise UnsupportedFormatError(dest, f"Detected format {detected.value} is not allowed")

        return dest

    def load(self, path: Path | str) -> PointCloud:
        """Загружает облако точек из файла через фабрику readers."""
        file_path = Path(path)
        if not file_path.exists():
            raise UploadError(f"File not found: {file_path}")
        reader = create_reader(file_path)
        return reader.read()

    def load_header(self, path: Path | str) -> PointCloudHeader:
        """Читает только заголовок файла."""
        file_path = Path(path)
        reader = create_reader(file_path)
        return reader.read_header()

    def save_and_load(self, filename: str, content: bytes) -> tuple[Path, PointCloud]:
        """Сохраняет upload и сразу загружает PointCloud."""
        saved = self.save_upload(filename, content)
        return saved, self.load(saved)
