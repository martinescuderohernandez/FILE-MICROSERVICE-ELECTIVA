"""Mapeo dominio -> esquemas HTTP."""

from __future__ import annotations

from app.domain.model.file_operations import FileResult
from app.entrypoint.rest.schemas import DocumentResponse, PhotoResponse


def to_photo_response(result: FileResult) -> PhotoResponse:
    return PhotoResponse(
        file_name=result.file.file_name,
        content_type=result.file.content_type,
        size_bytes=result.file.size_bytes,
        updated_at=result.file.last_modified,
        download_url=result.download_url,
    )


def to_document_response(result: FileResult) -> DocumentResponse:
    if not result.resource_id:
        raise ValueError("Un documento requiere resource_id")
    return DocumentResponse(
        document_id=result.resource_id,
        file_name=result.file.file_name,
        content_type=result.file.content_type,
        size_bytes=result.file.size_bytes,
        uploaded_at=result.file.last_modified,
        download_url=result.download_url,
    )
