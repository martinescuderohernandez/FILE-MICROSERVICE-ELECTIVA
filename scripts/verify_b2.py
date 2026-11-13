"""Verifica la conexion con Backblaze B2 sin pasar por la API HTTP.

Uso:
    python -m scripts.verify_b2
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

from app.application.service.file_metadata import (
    ORIGINAL_NAME_METADATA_KEY,
    encode_original_name,
)
from app.config import get_settings
from app.infrastructure.adapter.storage.b2_storage_adapter import B2StorageAdapter


async def main() -> None:
    settings = get_settings()
    storage = B2StorageAdapter(settings)
    key = f"_diagnostics/{uuid4().hex}.txt"
    payload = b"file-microservice diagnostic"

    print(f"Bucket:   {settings.b2_bucket_name}")
    print(f"Endpoint: {settings.b2_endpoint_url}")
    print(f"Region:   {settings.b2_region}")

    try:
        stored = await storage.put(
            key,
            payload,
            "text/plain",
            {ORIGINAL_NAME_METADATA_KEY: encode_original_name("diagnostico.txt")},
        )
        print(f"PUT OK    -> {stored.key} ({stored.size_bytes} bytes)")

        head = await storage.head(key)
        print(f"HEAD OK   -> {head.file_name if head else 'no encontrado'}")

        url = await storage.presigned_get_url(key, settings.presigned_url_ttl_seconds)
        print(f"PRESIGN OK-> {url[:90]}...")

        removed = await storage.delete(key)
        print(f"DELETE OK -> {removed}")
    finally:
        await storage.aclose()


if __name__ == "__main__":
    asyncio.run(main())
