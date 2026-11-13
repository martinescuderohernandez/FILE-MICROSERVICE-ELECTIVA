"""Codificacion del nombre original en metadata del objeto B2."""

from __future__ import annotations

import base64
import binascii

ORIGINAL_NAME_METADATA_KEY = "original-name-b64"

_DEFAULT_NAMES = {
    "image/jpeg": "photo.jpg",
    "image/png": "photo.png",
    "image/webp": "photo.webp",
    "application/pdf": "document.pdf",
}


def encode_original_name(file_name: str) -> str:
    """B2 solo acepta metadata ASCII; el nombre puede contener Unicode."""

    return base64.b64encode(file_name.encode("utf-8")).decode("ascii")


def decode_original_name(
    metadata: dict[str, str] | None,
    content_type: str | None,
) -> str:
    fallback = _DEFAULT_NAMES.get((content_type or "").lower(), "file")
    if not metadata:
        return fallback
    raw = metadata.get(ORIGINAL_NAME_METADATA_KEY)
    if not raw:
        return fallback
    try:
        return base64.b64decode(raw.encode("ascii")).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return fallback
