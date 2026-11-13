"""Casos de uso: documentos PDF multiples por usuario."""

from __future__ import annotations

from uuid import uuid4

from app.application.service.authorization import ensure_can_read, ensure_can_write
from app.application.service.file_metadata import ORIGINAL_NAME_METADATA_KEY, encode_original_name
from app.application.service.file_validator import FileValidator, sanitize_filename
from app.application.service.object_key_factory import ObjectKeyFactory
from app.domain.exception.errors import DocumentNotFoundError
from app.domain.model.actor import Actor
from app.domain.model.file_operations import DocumentPage, FileResult, UploadedFile
from app.domain.port.out.file_storage_port import FileStoragePort
from app.domain.port.out.user_client_port import UserClientPort
from app.domain.valueobject.document_id import DocumentId
from app.domain.valueobject.user_id import UserId


class DocumentService:
    """Sube, lista, consulta y elimina PDFs bajo ``.../documents/``.

    El id del documento es un UUID4 hexadecimal que forma parte de la clave.
    El nombre original viaja como metadata Base64 del objeto, de modo que no
    se requiere ninguna base de datos.
    """

    def __init__(
        self,
        storage: FileStoragePort,
        validator: FileValidator,
        user_client: UserClientPort,
        presigned_ttl_seconds: int,
        max_list_limit: int = 100,
    ) -> None:
        self._storage = storage
        self._validator = validator
        self._user_client = user_client
        self._ttl = presigned_ttl_seconds
        self._max_list_limit = max_list_limit
        self._keys = ObjectKeyFactory()

    async def upload(self, actor: Actor, user_id: str, upload: UploadedFile) -> FileResult:
        owner = UserId(user_id).value
        ensure_can_write(actor, owner)

        validated = self._validator.validate_document(upload.data)
        await self._user_client.ensure_exists(owner)

        document_id = DocumentId(uuid4().hex).value
        file_name = sanitize_filename(upload.file_name, "document.pdf")
        key = self._keys.document_key(owner, document_id)

        stored = await self._storage.put(
            key=key,
            data=upload.data,
            content_type=validated.content_type,
            metadata={ORIGINAL_NAME_METADATA_KEY: encode_original_name(file_name)},
        )
        url = await self._storage.presigned_get_url(key, self._ttl)
        return FileResult(file=stored, download_url=url, resource_id=document_id)

    async def list(
        self,
        actor: Actor,
        user_id: str,
        limit: int,
        cursor: str | None = None,
    ) -> DocumentPage:
        owner = UserId(user_id).value
        ensure_can_read(actor, owner)

        safe_limit = max(1, min(limit, self._max_list_limit))
        page = await self._storage.list(
            prefix=self._keys.document_prefix(owner),
            cursor=cursor,
            limit=safe_limit,
        )

        items: list[FileResult] = []
        for stored in page.items:
            document_id = self._keys.document_id_from_key(stored.key)
            if document_id is None:
                continue
            url = await self._storage.presigned_get_url(stored.key, self._ttl)
            items.append(FileResult(file=stored, download_url=url, resource_id=document_id))

        return DocumentPage(items=tuple(items), next_cursor=page.next_cursor)

    async def get(self, actor: Actor, user_id: str, document_id: str) -> FileResult:
        owner = UserId(user_id).value
        ensure_can_read(actor, owner)

        key = self._keys.document_key(owner, document_id)
        stored = await self._storage.head(key)
        if stored is None:
            raise DocumentNotFoundError(document_id)

        url = await self._storage.presigned_get_url(key, self._ttl)
        return FileResult(file=stored, download_url=url, resource_id=document_id)

    async def delete(self, actor: Actor, user_id: str, document_id: str) -> None:
        owner = UserId(user_id).value
        ensure_can_write(actor, owner)

        key = self._keys.document_key(owner, document_id)
        stored = await self._storage.head(key)
        if stored is None:
            raise DocumentNotFoundError(document_id)
        await self._storage.delete(key)
