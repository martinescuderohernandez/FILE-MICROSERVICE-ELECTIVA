"""Objeto almacenado en B2 (sin metadatos persistidos en base de datos)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class StoredFile:
    """Representacion de un objeto S3/B2.

    ``file_name`` es el nombre original que envio el cliente. Se guarda como
    metadata del objeto (Base64) porque no existe base de datos.
    """

    key: str
    file_name: str
    content_type: str
    size_bytes: int
    last_modified: datetime | None = None
    etag: str | None = None
