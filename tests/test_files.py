"""Tests de eliminacion masiva y de la verificacion opcional de usuarios."""

from __future__ import annotations

from tests.fake_storage import AlwaysExistsUserClient, RejectingUserClient
from tests.samples import PDF, PNG

PHOTO_URL = "/api/files/users/user-1/photo"
DOCS_URL = "/api/files/users/user-1/documents"
ALL_URL = "/api/files/users/user-1/files"


async def test_delete_all_removes_photo_and_documents(
    make_context, client_factory, auth_headers
):
    context = make_context()
    headers = auth_headers("user-1")

    async with client_factory(context) as client:
        await client.post(PHOTO_URL, headers=headers, files={"file": ("a.png", PNG, "image/png")})
        for name in ("uno.pdf", "dos.pdf"):
            await client.post(DOCS_URL, headers=headers, files={"file": (name, PDF, "application/pdf")})

        assert len(context.storage.objects) == 3

        response = await client.delete(ALL_URL, headers=headers)

        assert response.status_code == 200
        assert response.json()["deletedCount"] == 3
        assert context.storage.objects == {}


async def test_delete_all_is_idempotent(make_context, client_factory, auth_headers):
    context = make_context()

    async with client_factory(context) as client:
        response = await client.delete(ALL_URL, headers=auth_headers("user-1"))

    assert response.status_code == 200
    assert response.json()["deletedCount"] == 0


async def test_delete_all_forbidden_for_other_member(
    make_context, client_factory, auth_headers
):
    context = make_context()

    async with client_factory(context) as client:
        response = await client.delete(ALL_URL, headers=auth_headers("user-2"))

    assert response.status_code == 403


async def test_user_existence_client_is_called_on_upload(make_context, client_factory, auth_headers):
    user_client = AlwaysExistsUserClient()
    context = make_context(user_client=user_client)

    async with client_factory(context) as client:
        response = await client.post(
            PHOTO_URL,
            headers=auth_headers("user-1"),
            files={"file": ("a.png", PNG, "image/png")},
        )

    assert response.status_code == 201
    assert user_client.checked == ["user-1"]


async def test_unknown_user_returns_404_when_verification_is_enabled(
    make_context, client_factory, auth_headers
):
    context = make_context(user_client=RejectingUserClient())

    async with client_factory(context) as client:
        response = await client.post(
            PHOTO_URL,
            headers=auth_headers("user-1"),
            files={"file": ("a.png", PNG, "image/png")},
        )

    assert response.status_code == 404
    assert response.json()["code"] == "user_not_found"
    assert context.storage.objects == {}
