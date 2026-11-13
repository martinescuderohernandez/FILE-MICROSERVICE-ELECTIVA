"""Implementacion en memoria del puerto de almacenamiento para tests."""

from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timezone
from typing import Mapping
from urllib.parse import quote

from app.application.service.file_metadata import decode_original_name
from app.domain.model.file_page import FilePage
from app.domain.model.stored_file import StoredFile
from app.domain.port.out.file_storage_port import FileStoragePort
from app.domain.port.out.user_client_port import UserClientPort


class FakeStorage(FileStoragePort):
    def __init__(self) -> None:
        self.objects: dict[str, dict] = {}

    async def put(
        self,
        key: str,
        data: bytes,
        content_type: str,
        metadata: Mapping[str, str] | None = None,
    ) -> StoredFile:
        entry = {
            "data": data,
            "content_type": content_type,
            "metadata": {str(k).lower(): str(v) for k, v in (metadata or {}).items()},
            "last_modified": datetime.now(timezone.utc),
            "etag": hashlib.md5(data).hexdigest(),
        }
        self.objects[key] = entry
        return StoredFile(
            key=key,
            file_name=decode_original_name(entry["metadata"], content_type),
            content_type=content_type,
            size_bytes=len(data),
            last_modified=entry["last_modified"],
            etag=entry["etag"],
        )

    async def head(self, key: str) -> StoredFile | None:
        entry = self.objects.get(key)
        if entry is None:
            return None
        return StoredFile(
            key=key,
            file_name=decode_original_name(entry["metadata"], entry["content_type"]),
            content_type=entry["content_type"],
            size_bytes=len(entry["data"]),
            last_modified=entry["last_modified"],
            etag=entry["etag"],
        )

    async def list(
        self,
        prefix: str,
        cursor: str | None = None,
        limit: int = 100,
    ) -> FilePage:
        keys = sorted(key for key in self.objects if key.startswith(prefix))
        start = int(base64.urlsafe_b64decode(cursor).decode()) if cursor else 0
        page_keys = keys[start : start + limit]
        next_start = start + limit
        next_cursor = (
            base64.urlsafe_b64encode(str(next_start).encode()).decode()
            if next_start < len(keys)
            else None
        )

        items = []
        for key in page_keys:
            stored = await self.head(key)
            if stored is not None:
                items.append(stored)
        return FilePage(items=tuple(items), next_cursor=next_cursor)

    async def delete(self, key: str) -> bool:
        return self.objects.pop(key, None) is not None

    async def delete_prefix(self, prefix: str) -> int:
        keys = [key for key in self.objects if key.startswith(prefix)]
        for key in keys:
            del self.objects[key]
        return len(keys)

    async def presigned_get_url(self, key: str, expires_in: int) -> str:
        return f"https://b2.fake/{quote(key)}?X-Amz-Expires={expires_in}"


class AlwaysExistsUserClient(UserClientPort):
    def __init__(self) -> None:
        self.checked: list[str] = []

    async def ensure_exists(self, user_id: str) -> None:
        self.checked.append(user_id)


class RejectingUserClient(UserClientPort):
    """Simula que el user-microservice responde 404."""

    async def ensure_exists(self, user_id: str) -> None:
        from app.domain.exception.errors import UserNotFoundError

        raise UserNotFoundError(user_id)
