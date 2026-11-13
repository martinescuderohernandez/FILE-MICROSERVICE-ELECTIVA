"""Esquemas de respuesta HTTP (camelCase para el frontend)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


def _to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(word.capitalize() for word in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=_to_camel, populate_by_name=True)


class PhotoResponse(ApiModel):
    file_name: str
    content_type: str
    size_bytes: int
    updated_at: datetime | None
    download_url: str


class DocumentResponse(ApiModel):
    document_id: str
    file_name: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime | None
    download_url: str


class DocumentListResponse(ApiModel):
    items: list[DocumentResponse]
    next_cursor: str | None = None


class DeleteAllResponse(ApiModel):
    deleted_count: int


class HealthResponse(ApiModel):
    status: str
    service: str
    version: str
    environment: str


class ErrorResponse(ApiModel):
    detail: str
    code: str


class MessageResponse(ApiModel):
    detail: str
