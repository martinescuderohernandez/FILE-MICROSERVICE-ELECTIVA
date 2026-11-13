"""Tests de configuracion y decodificacion del secreto compartido."""

from __future__ import annotations

import base64

import pytest
from pydantic import ValidationError

from app.config import Settings, decode_jwt_secret

UNPADDED_SECRET = base64.b64encode(b"secreto-de-pruebas-con-32-bytes!!").decode().rstrip("=")


def test_decodes_base64_without_padding_like_java():
    key = decode_jwt_secret(UNPADDED_SECRET)

    assert key == b"secreto-de-pruebas-con-32-bytes!!"
    assert len(key) >= 32


def test_rejects_non_base64_secret():
    with pytest.raises(ValueError, match="Base64"):
        decode_jwt_secret("no es base64 !!!")


def test_rejects_short_secret():
    short = base64.b64encode(b"corto").decode()

    with pytest.raises(ValueError, match="32 bytes"):
        decode_jwt_secret(short)


def test_settings_validate_secret_at_startup():
    with pytest.raises(ValidationError):
        Settings(jwt_secret=base64.b64encode(b"corto").decode())


def test_default_limit_never_exceeds_max():
    settings = Settings(
        jwt_secret=base64.b64encode(b"x" * 48).decode(),
        max_list_limit=30,
        default_list_limit=90,
    )

    assert settings.default_list_limit == 30


def test_cors_origins_are_split():
    settings = Settings(
        jwt_secret=base64.b64encode(b"x" * 48).decode(),
        cors_origins="https://a.com, https://b.com",
    )

    assert settings.cors_origin_list == ["https://a.com", "https://b.com"]


def test_cors_wildcard():
    settings = Settings(jwt_secret=base64.b64encode(b"x" * 48).decode(), cors_origins="*")

    assert settings.cors_origin_list == ["*"]
