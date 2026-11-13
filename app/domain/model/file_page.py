"""Pagina de objetos devuelta por el almacenamiento."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.model.stored_file import StoredFile


@dataclass(frozen=True, slots=True)
class FilePage:
    items: tuple[StoredFile, ...]
    next_cursor: str | None = None
