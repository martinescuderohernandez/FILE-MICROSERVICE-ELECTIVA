"""Actor autenticado (dueño del token JWT)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    ADMIN = "ADMIN"
    REVIEWER = "REVIEWER"
    MEMBER = "MEMBER"

    @classmethod
    def from_claim(cls, value: object) -> Role:
        if not isinstance(value, str):
            raise ValueError("El claim 'role' es obligatorio")
        try:
            return cls(value.strip().upper())
        except ValueError as exc:
            raise ValueError(f"Rol no soportado: {value!r}") from exc


@dataclass(frozen=True, slots=True)
class Actor:
    """Identidad que ejecuta una operacion."""

    user_id: str
    role: Role

    @property
    def is_admin(self) -> bool:
        return self.role is Role.ADMIN

    @property
    def can_review(self) -> bool:
        return self.role in (Role.ADMIN, Role.REVIEWER)
