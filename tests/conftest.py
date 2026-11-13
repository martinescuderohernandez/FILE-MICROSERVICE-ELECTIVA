"""Fixtures compartidas por la suite."""

from __future__ import annotations

import base64
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import AsyncIterator

import jwt
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.config import DEV_JWT_SECRET, Settings, decode_jwt_secret
from app.main import create_app
from tests.fake_storage import FakeStorage

JWT_KEY = decode_jwt_secret(DEV_JWT_SECRET)


@dataclass
class TestContext:
    app: FastAPI
    storage: FakeStorage
    settings: Settings


def build_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "jwt_secret": DEV_JWT_SECRET,
        "b2_key_id": "test-key-id",
        "b2_application_key": "test-application-key",
        "b2_bucket_name": "test-bucket",
        "user_service_enabled": False,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


@pytest.fixture
def make_context():
    def _make(user_client=None, **settings_overrides: object) -> TestContext:
        settings = build_settings(**settings_overrides)
        storage = FakeStorage()
        app = create_app(settings=settings, storage=storage, user_client=user_client)
        return TestContext(app=app, storage=storage, settings=settings)

    return _make


@pytest.fixture
async def client(make_context) -> AsyncIterator[AsyncClient]:
    context = make_context()
    transport = ASGITransport(app=context.app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


@pytest.fixture
def client_factory():
    @asynccontextmanager
    async def _factory(context: TestContext) -> AsyncIterator[AsyncClient]:
        transport = ASGITransport(app=context.app)
        async with AsyncClient(transport=transport, base_url="http://test") as http_client:
            yield http_client

    return _factory


@pytest.fixture
def auth_headers():
    def _headers(
        user_id: str = "user-1",
        role: str = "MEMBER",
        *,
        secret: str = DEV_JWT_SECRET,
        expires_in: int = 900,
    ) -> dict[str, str]:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "role": role,
            "iat": now,
            "exp": now + timedelta(seconds=expires_in),
        }
        token = jwt.encode(payload, decode_jwt_secret(secret), algorithm="HS256")
        return {"Authorization": f"Bearer {token}"}

    return _headers


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")
