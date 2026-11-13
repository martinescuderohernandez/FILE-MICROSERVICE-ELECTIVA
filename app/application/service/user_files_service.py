"""Caso de uso: eliminar todos los archivos de un usuario."""

from __future__ import annotations

from app.application.service.authorization import ensure_can_write
from app.application.service.object_key_factory import ObjectKeyFactory
from app.domain.model.actor import Actor
from app.domain.port.out.file_storage_port import FileStoragePort
from app.domain.valueobject.user_id import UserId


class UserFilesService:
    """Elimina foto y documentos de un usuario en una sola operacion."""

    def __init__(self, storage: FileStoragePort) -> None:
        self._storage = storage
        self._keys = ObjectKeyFactory()

    async def delete_all(self, actor: Actor, user_id: str) -> int:
        owner = UserId(user_id).value
        ensure_can_write(actor, owner)
        return await self._storage.delete_prefix(self._keys.user_prefix(owner))
