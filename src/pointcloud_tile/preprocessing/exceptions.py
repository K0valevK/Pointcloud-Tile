"""Исключения модуля предобработки."""

from pathlib import Path


class PreprocessingError(Exception):
    """Базовое исключение предобработки."""


class UnsupportedFormatError(PreprocessingError):
    """Формат файла не поддерживается."""

    def __init__(self, path: Path | str, message: str | None = None) -> None:
        self.path = Path(path)
        detail = message or f"Unsupported point cloud format: {self.path.suffix}"
        super().__init__(f"{detail} ({self.path})")


class FormatDetectionError(PreprocessingError):
    """Не удалось определить формат файла."""


class ReaderError(PreprocessingError):
    """Ошибка чтения облака точек."""

    def __init__(self, path: Path | str, message: str, cause: Exception | None = None) -> None:
        self.path = Path(path)
        self.cause = cause
        suffix = f": {cause}" if cause else ""
        super().__init__(f"Failed to read {self.path}: {message}{suffix}")


class WriterError(PreprocessingError):
    """Ошибка записи облака точек."""

    def __init__(self, path: Path | str, message: str, cause: Exception | None = None) -> None:
        self.path = Path(path)
        self.cause = cause
        suffix = f": {cause}" if cause else ""
        super().__init__(f"Failed to write {self.path}: {message}{suffix}")


class InvalidPointCloudError(PreprocessingError):
    """Некорректная структура или содержимое PointCloud."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class UploadError(PreprocessingError):
    """Ошибка загрузки файла."""

    def __init__(self, message: str, filename: str | None = None) -> None:
        self.filename = filename
        super().__init__(message)
