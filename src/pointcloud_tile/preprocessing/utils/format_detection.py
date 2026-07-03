"""Определение формата облака точек по расширению и magic bytes."""

from pathlib import Path

from pointcloud_tile.preprocessing.exceptions import FormatDetectionError, UnsupportedFormatError
from pointcloud_tile.preprocessing.models.enums import PointCloudFormat

LAS_MAGIC = b"LASF"
PLY_MAGIC = b"ply"


def is_las_family(header_bytes: bytes) -> bool:
    return len(header_bytes) >= 4 and header_bytes[:4] == LAS_MAGIC


def is_ply(header_bytes: bytes) -> bool:
    return header_bytes.startswith(PLY_MAGIC)


def _is_laz_file(path: Path, header_bytes: bytes) -> bool:
    if path.suffix.lower() == ".laz":
        return True
    if path.suffix.lower() == ".las":
        return False
    # LAZ использует тот же заголовок LASF; проверяем флаг сжатия в заголовке LAS 1.4
    if len(header_bytes) >= 32:
        # Offset 32-33: point data format (бит 7 = compressed в некоторых реализациях)
        # Надёжнее полагаться на laspy при неоднозначности
        try:
            import laspy

            with laspy.open(path) as reader:
                return bool(getattr(reader.header, "are_points_compressed", False))
        except Exception:
            return path.suffix.lower() == ".laz"
    return path.suffix.lower() == ".laz"


def detect_format_from_bytes(data: bytes, path_hint: Path | None = None) -> PointCloudFormat:
    """Определяет формат по первым байтам файла."""
    if is_ply(data):
        return PointCloudFormat.PLY

    if is_las_family(data):
        if path_hint is not None:
            return (
                PointCloudFormat.LAZ
                if _is_laz_file(path_hint, data)
                else PointCloudFormat.LAS
            )
        return PointCloudFormat.LAZ if _looks_like_laz_payload(data) else PointCloudFormat.LAS

    raise FormatDetectionError(f"Unknown format (magic: {data[:8]!r})")


def _looks_like_laz_payload(data: bytes) -> bool:
    """Эвристика: LAZ часто содержит маркер laszip в заголовке/метаданных."""
    return b"laszip" in data[:512].lower()


def detect_format_from_path(path: Path | str) -> PointCloudFormat | None:
    """Определяет формат по расширению файла."""
    return PointCloudFormat.from_extension(Path(path).suffix)


def detect_format(path: Path | str, *, sniff_bytes: int = 512) -> PointCloudFormat:
    """
    Автоматическое определение формата: расширение → magic bytes → laspy.

    Raises:
        UnsupportedFormatError: формат не поддерживается.
        FormatDetectionError: формат не удалось определить.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise UnsupportedFormatError(file_path, "File does not exist")

    by_extension = detect_format_from_path(file_path)
    header = file_path.read_bytes()[:sniff_bytes]

    if by_extension is not None:
        if by_extension == PointCloudFormat.PLY and not is_ply(header):
            raise FormatDetectionError(f"Extension .ply but magic bytes mismatch for {file_path}")
        if by_extension in {PointCloudFormat.LAS, PointCloudFormat.LAZ} and not is_las_family(
            header
        ):
            raise FormatDetectionError(f"Extension {by_extension.extension} but not LASF for {file_path}")
        return by_extension

    try:
        return detect_format_from_bytes(header, path_hint=file_path)
    except FormatDetectionError as exc:
        raise UnsupportedFormatError(file_path, str(exc)) from exc
