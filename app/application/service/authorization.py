"""Reglas de autorizacion basadas en el rol del JWT."""

from __future__ import annotations

from app.domain.exception.errors import ForbiddenError
from app.domain.model.actor import Actor


def ensure_can_read(actor: Actor, owner_user_id: str) -> None:
    """Dueño, ADMIN o REVIEWER pueden leer."""

    if actor.user_id == owner_user_id or actor.can_review:
        return
    raise ForbiddenError("Solo el dueño, un ADMIN o un REVIEWER puede consultar estos archivos")


def ensure_can_write(actor: Actor, owner_user_id: str) -> None:
    """Dueño o ADMIN pueden subir/eliminar."""

    if actor.user_id == owner_user_id or actor.is_admin:
        return
    raise ForbiddenError("Solo el dueño o un ADMIN puede modificar estos archivos")
