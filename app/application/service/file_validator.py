"""Validacion del contenido real de los archivos (magic bytes)."""

from __future__ import annotations

import re
from dataclasses import dataclass

import filetype

from app.domain.exception.errors import EmptyFileError, FileTooLargeError, InvalidFileTypeError
from app.domain.valueobject.file_category import FileCategory

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_MAX_FILE_NAME_LENGTH = 200

_PHOTO_MIME_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

_PDF_MIME_TYPE = "application/pdf"


@dataclass(frozen=True, slots=True)
class ValidatedFile:
    content_type: str
    extension: str


def sanitize_filename(raw: str | None, fallback: str) -> str:
    """Quita rutas y caracteres de control del nombre enviado por el cliente."""

    if not raw:
        return fallback
    name = raw.replace("\\", "/").rsplit("/", 1)[-1]
    name = _CONTROL_CHARS.sub("", name).strip()
    if not name or name in {".", ".."}:
        return fallback
    return name[:_MAX_FILE_NAME_LENGTH]


class FileValidator:
    """Valida tamano y tipo real usando los primeros bytes del archivo."""

    def __init__(self, max_photo_bytes: int, max_document_bytes: int) -> None:
        self._max_photo_bytes = max_photo_bytes
        self._max_document_bytes = max_document_bytes

    def validate_photo(self, data: bytes) -> ValidatedFile:
        self._check_common(data, self._max_photo_bytes, FileCategory.PHOTO)
        detected = self._detect(data)
        if detected is None or detected.content_type not in _PHOTO_MIME_TYPES:
            raise InvalidFileTypeError(FileCategory.PHOTO.allowed_description)
        return detected

    def validate_document(self, data: bytes) -> ValidatedFile:
        self._check_common(data, self._max_document_bytes, FileCategory.DOCUMENT)
        detected = self._detect(data)
        if detected is None or detected.content_type != _PDF_MIME_TYPE:
            raise InvalidFileTypeError(FileCategory.DOCUMENT.allowed_description)
        return detected

    @staticmethod
    def _check_common(data: bytes, max_bytes: int, category: FileCategory) -> None:
        if not data:
            raise EmptyFileError()
        if len(data) > max_bytes:
            raise FileTooLargeError(max_bytes, category.value)

    @staticmethod
    def _detect(data: bytes) -> ValidatedFile | None:
        # filetype inspecciona magic bytes, no la extension ni el Content-Type declarado.
        kind = filetype.guess(data)
        if kind is not None:
            mime = (kind.mime or "").lower()
            if mime == "image/jpg":
                mime = "image/jpeg"
            extension = kind.extension or ""
            if mime in _PHOTO_MIME_TYPES:
                return ValidatedFile(mime, _PHOTO_MIME_TYPES[mime])
            if mime == _PDF_MIME_TYPE:
                return ValidatedFile(mime, extension or "pdf")

        # Respaldo explicito para PDFs truncados que filetype no alcanza a clasificar.
        if data.lstrip().startswith(b"%PDF-"):
            return ValidatedFile(_PDF_MIME_TYPE, "pdf")
        return None
