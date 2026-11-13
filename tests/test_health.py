"""Tests de salud y de la documentacion OpenAPI."""

from __future__ import annotations


async def test_health_does_not_require_auth_or_b2(client):
    response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "file-microservice"
    assert body["version"] == "1.0.0"


async def test_root_lists_entrypoints(client):
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"


async def test_openapi_exposes_bearer_security(client):
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert "/api/files/users/{user_id}/photo" in schema["paths"]
    assert "HTTPBearer" in schema["components"]["securitySchemes"]
