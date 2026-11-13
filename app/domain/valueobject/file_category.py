"""Categorias de archivo soportadas."""

from __future__ import annotations

from enum import Enum


class FileCategory(str, Enum):
    PHOTO = "photo"
    DOCUMENT = "document"

    @property
    def allowed_description(self) -> str:
        if self is FileCategory.PHOTO:
            return "JPEG, PNG y WebP"
        return "PDF"
