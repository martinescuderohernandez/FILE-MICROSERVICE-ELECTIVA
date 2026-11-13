"""Lectura controlada de archivos multipart."""

from __future__ import annotations

from fastapi import UploadFile

from app.domain.exception.errors import FileTooLargeError
from app.domain.model.file_operations import UploadedFile
from app.domain.valueobject.file_category import FileCategory


async def read_upload(file: UploadFile, max_bytes: int, category: FileCategory) -> UploadedFile:
    """Lee como maximo ``max_bytes + 1`` para detectar excesos sin OOM."""

    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise FileTooLargeError(max_bytes, category.value)

    return UploadedFile(
        data=data,
        file_name=file.filename or "",
        declared_content_type=file.content_type,
    )
