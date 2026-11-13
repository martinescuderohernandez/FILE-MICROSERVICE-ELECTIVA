"""Identificador de usuario validado."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar

from app.domain.exception.errors import InvalidUserIdError

_USER_ID_PATTERN: re.Pattern[str] = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


@dataclass(frozen=True, slots=True)
class UserId:
    """Id de usuario emitido por el user-microservice.

    Se restringe a caracteres seguros porque forma parte del prefijo S3.
    Evita secuencias como ``../`` o claves vacias.
    """

    value: str
    PATTERN: ClassVar[re.Pattern[str]] = _USER_ID_PATTERN

    def __post_init__(self) -> None:
        if (
            not isinstance(self.value, str)
            or not self.PATTERN.fullmatch(self.value)
            or self.value in {".", ".."}
        ):
            raise InvalidUserIdError(str(self.value))

    def __str__(self) -> str:
        return self.value
