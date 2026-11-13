"""Identificador opaco de documento."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar

from app.domain.exception.errors import InvalidDocumentIdError

_DOCUMENT_ID_PATTERN: re.Pattern[str] = re.compile(r"^[a-f0-9]{32}$")


@dataclass(frozen=True, slots=True)
class DocumentId:
    """UUID4 en formato hexadecimal sin guiones (32 caracteres)."""

    value: str
    PATTERN: ClassVar[re.Pattern[str]] = _DOCUMENT_ID_PATTERN

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.PATTERN.fullmatch(self.value):
            raise InvalidDocumentIdError(str(self.value))

    def __str__(self) -> str:
        return self.value
