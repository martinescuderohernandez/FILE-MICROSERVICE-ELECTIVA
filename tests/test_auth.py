"""Tests de autenticacion JWT compartida con user-microservice."""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.config import DEV_JWT_SECRET, decode_jwt_secret

OTHER_SECRET = base64.b64encode(b"otro-secreto-de-32-bytes-para-pruebas!!").decode()
PHOTO_URL = "/api/files/users/user-1/photo"


async def test_missing_token_returns_401(client):
    response = await client.get(PHOTO_URL)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


async def test_invalid_token_returns_401(client):
    response = await client.get(PHOTO_URL, headers={"Authorization": "Bearer no-es-un-jwt"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Token invalido"


async def test_expired_token_returns_401(client, auth_headers):
    headers = auth_headers(expires_in=-60)

    response = await client.get(PHOTO_URL, headers=headers)

    assert response.status_code == 401
    assert "expiro" in response.json()["detail"]


async def test_token_signed_with_other_secret_returns_401(client, auth_headers):
    headers = auth_headers(secret=OTHER_SECRET)

    response = await client.get(PHOTO_URL, headers=headers)

    assert response.status_code == 401


async def test_unknown_role_returns_401(client):
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {"sub": "user-1", "role": "SUPERUSER", "exp": now + timedelta(minutes=5)},
        decode_jwt_secret(DEV_JWT_SECRET),
        algorithm="HS256",
    )

    response = await client.get(PHOTO_URL, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


async def test_token_without_role_returns_401(client):
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {"sub": "user-1", "exp": now + timedelta(minutes=5)},
        decode_jwt_secret(DEV_JWT_SECRET),
        algorithm="HS256",
    )

    response = await client.get(PHOTO_URL, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


@pytest.mark.parametrize("subject", ["bad user", "", "x" * 65])
async def test_invalid_subject_returns_401(client, subject):
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {"sub": subject, "role": "MEMBER", "exp": now + timedelta(minutes=5)},
        decode_jwt_secret(DEV_JWT_SECRET),
        algorithm="HS256",
    )

    response = await client.get(
        f"/api/files/users/{subject or 'x'}/photo",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
