"""Adaptador de almacenamiento para Backblaze B2 (API S3)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Mapping

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.application.service.file_metadata import decode_original_name
from app.config import Settings
from app.domain.exception.errors import StorageError
from app.domain.model.file_page import FilePage
from app.domain.model.stored_file import StoredFile
from app.domain.port.out.file_storage_port import FileStoragePort

logger = logging.getLogger(__name__)

_NOT_FOUND_CODES = {"404", "NoSuchKey", "NotFound", "NoSuchBucket"}
_MAX_DELETE_BATCH = 1000


def _is_not_found(error: ClientError) -> bool:
    response = getattr(error, "response", {}) or {}
    code = str(response.get("Error", {}).get("Code", ""))
    status = str(response.get("ResponseMetadata", {}).get("HTTPStatusCode", ""))
    return code in _NOT_FOUND_CODES or status == "404"


def _clean_etag(value: Any) -> str | None:
    if not value:
        return None
    return str(value).strip('"')


class B2StorageAdapter(FileStoragePort):
    """Implementacion con ``boto3`` apuntando al endpoint S3 de B2.

    El cliente se crea de forma perezosa. ``/health`` nunca toca B2, por lo que
    la aplicacion puede arrancar aunque las credenciales aun no esten cargadas.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client_instance: Any | None = None
        self._client_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Cliente boto3
    # ------------------------------------------------------------------
    def _build_client(self) -> Any:
        if not self._settings.b2_credentials_configured:
            raise StorageError(
                "Faltan B2_KEY_ID y B2_APPLICATION_KEY. Configure las credenciales "
                "de la Application Key de Backblaze B2."
            )
        config = Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            retries={"max_attempts": 3, "mode": "standard"},
            connect_timeout=5,
            read_timeout=60,
        )
        return boto3.client(
            "s3",
            endpoint_url=self._settings.b2_endpoint_url,
            region_name=self._settings.b2_region,
            aws_access_key_id=self._settings.b2_key_id,
            aws_secret_access_key=self._settings.b2_application_key,
            config=config,
        )

    async def _client(self) -> Any:
        if self._client_instance is None:
            async with self._client_lock:
                if self._client_instance is None:
                    self._client_instance = await asyncio.to_thread(self._build_client)
        return self._client_instance

    def _bucket(self) -> str:
        return self._settings.b2_bucket_name

    # ------------------------------------------------------------------
    # Operaciones del puerto
    # ------------------------------------------------------------------
    async def put(
        self,
        key: str,
        data: bytes,
        content_type: str,
        metadata: Mapping[str, str] | None = None,
    ) -> StoredFile:
        client = await self._client()
        safe_metadata = {str(k).lower(): str(v) for k, v in (metadata or {}).items()}

        def _put() -> dict[str, Any]:
            return client.put_object(
                Bucket=self._bucket(),
                Key=key,
                Body=data,
                ContentType=content_type,
                Metadata=safe_metadata,
            )

        try:
            response = await asyncio.to_thread(_put)
        except (ClientError, BotoCoreError) as exc:
            raise StorageError(f"No fue posible subir el archivo a B2: {exc}") from exc

        file_name = decode_original_name(safe_metadata, content_type)
        return StoredFile(
            key=key,
            file_name=file_name,
            content_type=content_type,
            size_bytes=len(data),
            last_modified=datetime.now(timezone.utc),
            etag=_clean_etag(response.get("ETag")),
        )

    async def head(self, key: str) -> StoredFile | None:
        client = await self._client()

        def _head() -> dict[str, Any]:
            return client.head_object(Bucket=self._bucket(), Key=key)

        try:
            response = await asyncio.to_thread(_head)
        except ClientError as exc:
            if _is_not_found(exc):
                return None
            raise StorageError(f"No fue posible consultar el objeto en B2: {exc}") from exc
        except BotoCoreError as exc:
            raise StorageError(f"No fue posible consultar el objeto en B2: {exc}") from exc

        content_type = response.get("ContentType") or "application/octet-stream"
        metadata = response.get("Metadata") or {}
        return StoredFile(
            key=key,
            file_name=decode_original_name(metadata, content_type),
            content_type=content_type,
            size_bytes=int(response.get("ContentLength") or 0),
            last_modified=response.get("LastModified"),
            etag=_clean_etag(response.get("ETag")),
        )

    async def list(
        self,
        prefix: str,
        cursor: str | None = None,
        limit: int = 100,
    ) -> FilePage:
        client = await self._client()

        def _list() -> dict[str, Any]:
            params: dict[str, Any] = {
                "Bucket": self._bucket(),
                "Prefix": prefix,
                "MaxKeys": max(1, min(limit, 1000)),
            }
            if cursor:
                params["ContinuationToken"] = cursor
            return client.list_objects_v2(**params)

        try:
            response = await asyncio.to_thread(_list)
        except (ClientError, BotoCoreError) as exc:
            raise StorageError(f"No fue posible listar los archivos en B2: {exc}") from exc

        contents = response.get("Contents") or []
        heads = await asyncio.gather(
            *(self.head(str(item["Key"])) for item in contents),
            return_exceptions=True,
        )

        items: list[StoredFile] = []
        for item, head in zip(contents, heads):
            if isinstance(head, Exception) or head is None:
                # El objeto pudo eliminarse entre list y head; se omite.
                continue
            items.append(head)

        # Mas recientes primero dentro de la pagina.
        items.sort(key=lambda stored: stored.last_modified or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        next_cursor = response.get("NextContinuationToken")
        return FilePage(items=tuple(items), next_cursor=str(next_cursor) if next_cursor else None)

    async def delete(self, key: str) -> bool:
        client = await self._client()

        def _delete() -> None:
            client.delete_object(Bucket=self._bucket(), Key=key)

        try:
            await asyncio.to_thread(_delete)
        except (ClientError, BotoCoreError) as exc:
            raise StorageError(f"No fue posible eliminar el archivo en B2: {exc}") from exc
        return True

    async def delete_prefix(self, prefix: str) -> int:
        client = await self._client()

        keys: list[str] = []

        def _collect() -> None:
            token: str | None = None
            while True:
                params: dict[str, Any] = {
                    "Bucket": self._bucket(),
                    "Prefix": prefix,
                    "MaxKeys": 1000,
                }
                if token:
                    params["ContinuationToken"] = token
                response = client.list_objects_v2(**params)
                for item in response.get("Contents") or []:
                    keys.append(str(item["Key"]))
                if not response.get("IsTruncated"):
                    break
                token = response.get("NextContinuationToken")
                if not token:
                    break

        def _delete_batch(batch: list[str]) -> None:
            client.delete_objects(
                Bucket=self._bucket(),
                Delete={"Objects": [{"Key": key} for key in batch], "Quiet": True},
            )

        try:
            await asyncio.to_thread(_collect)
            for start in range(0, len(keys), _MAX_DELETE_BATCH):
                batch = keys[start : start + _MAX_DELETE_BATCH]
                await asyncio.to_thread(_delete_batch, batch)
        except (ClientError, BotoCoreError) as exc:
            raise StorageError(f"No fue posible eliminar los archivos en B2: {exc}") from exc

        return len(keys)

    async def presigned_get_url(self, key: str, expires_in: int) -> str:
        client = await self._client()

        def _presign() -> str:
            return client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket(), "Key": key},
                ExpiresIn=expires_in,
            )

        try:
            return await asyncio.to_thread(_presign)
        except (ClientError, BotoCoreError) as exc:
            raise StorageError(f"No fue posible generar la URL de descarga: {exc}") from exc

    async def aclose(self) -> None:
        if self._client_instance is not None:
            try:
                await asyncio.to_thread(self._client_instance.close)
            except Exception as exc:  # boto3 propaga errores variados al cerrar
                logger.debug("Error cerrando cliente B2: %s", exc)
            self._client_instance = None
