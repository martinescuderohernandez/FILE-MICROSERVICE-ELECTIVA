"""Caso de uso: foto de perfil unica por usuario."""

from __future__ import annotations

from app.application.service.authorization import ensure_can_read, ensure_can_write
from app.application.service.file_metadata import ORIGINAL_NAME_METADATA_KEY, encode_original_name
from app.application.service.file_validator import FileValidator, sanitize_filename
from app.application.service.object_key_factory import ObjectKeyFactory
from app.domain.exception.errors import PhotoNotFoundError
from app.domain.model.actor import Actor
from app.domain.model.file_operations import FileResult, UploadedFile
from app.domain.port.out.file_storage_port import FileStoragePort
from app.domain.port.out.user_client_port import UserClientPort
from app.domain.valueobject.user_id import UserId


class PhotoService:
    """Sube, consulta y elimina la foto unica en ``.../photos/profile``.

    Reemplazar la foto sobrescribe el mismo objeto; no se crean copias ni
    se persisten metadatos en base de datos.
    """

    def __init__(
        self,
        storage: FileStoragePort,
        validator: FileValidator,
        user_client: UserClientPort,
        presigned_ttl_seconds: int,
    ) -> None:
        self._storage = storage
        self._validator = validator
        self._user_client = user_client
        self._ttl = presigned_ttl_seconds
        self._keys = ObjectKeyFactory()

    async def upload(self, actor: Actor, user_id: str, upload: UploadedFile) -> FileResult:
        owner = UserId(user_id).value
        ensure_can_write(actor, owner)

        validated = self._validator.validate_photo(upload.data)
        await self._user_client.ensure_exists(owner)

        file_name = sanitize_filename(upload.file_name, f"photo.{validated.extension}")
        key = self._keys.photo_key(owner)

        stored = await self._storage.put(
            key=key,
            data=upload.data,
            content_type=validated.content_type,
            metadata={ORIGINAL_NAME_METADATA_KEY: encode_original_name(file_name)},
        )
        url = await self._storage.presigned_get_url(key, self._ttl)
        return FileResult(file=stored, download_url=url)

    async def get(self, actor: Actor, user_id: str) -> FileResult:
        owner = UserId(user_id).value
        ensure_can_read(actor, owner)

        key = self._keys.photo_key(owner)
        stored = await self._storage.head(key)
        if stored is None:
            raise PhotoNotFoundError()

        url = await self._storage.presigned_get_url(key, self._ttl)
        return FileResult(file=stored, download_url=url)

    async def delete(self, actor: Actor, user_id: str) -> None:
        owner = UserId(user_id).value
        ensure_can_write(actor, owner)

        key = self._keys.photo_key(owner)
        stored = await self._storage.head(key)
        if stored is None:
            raise PhotoNotFoundError()
        await self._storage.delete(key)
