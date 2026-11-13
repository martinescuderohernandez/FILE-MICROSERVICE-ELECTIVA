"""Estructuras de entrada/salida compartidas por los casos de uso."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.model.stored_file import StoredFile


@dataclass(frozen=True, slots=True)
class UploadedFile:
    """Archivo recibido por la capa REST antes de validarse."""

    data: bytes
    file_name: str
    declared_content_type: str | None = None


@dataclass(frozen=True, slots=True)
class FileResult:
    """Resultado de una operacion sobre un archivo.

    ``resource_id`` solo aplica a documentos; la foto es unica por usuario y
    no necesita identificador adicional.
    """

    file: StoredFile
    download_url: str
    resource_id: str | None = None


@dataclass(frozen=True, slots=True)
class DocumentPage:
    """Pagina de documentos de un usuario."""

    items: tuple[FileResult, ...]
    next_cursor: str | None = None
