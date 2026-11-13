"""Tests de la foto unica por usuario."""

from __future__ import annotations

from tests.samples import JPEG, PNG

PHOTO_URL = "/api/files/users/user-1/photo"


async def test_upload_get_replace_and_delete_photo(make_context, client_factory, auth_headers):
    context = make_context()
    headers = auth_headers("user-1")

    async with client_factory(context) as client:
        upload = await client.post(
            PHOTO_URL,
            headers=headers,
            files={"file": ("avatar.png", PNG, "image/png")},
        )
        assert upload.status_code == 201, upload.text
        body = upload.json()
        assert body["fileName"] == "avatar.png"
        assert body["contentType"] == "image/png"
        assert body["sizeBytes"] == len(PNG)
        assert body["downloadUrl"].startswith("https://b2.fake/")

        key = "users/user-1/photos/profile"
        assert list(context.storage.objects) == [key]

        fetched = await client.get(PHOTO_URL, headers=headers)
        assert fetched.status_code == 200
        assert fetched.json()["fileName"] == "avatar.png"

        replaced = await client.post(
            PHOTO_URL,
            headers=headers,
            files={"file": ("nueva.jpg", JPEG, "image/jpeg")},
        )
        assert replaced.status_code == 201
        assert replaced.json()["contentType"] == "image/jpeg"
        assert list(context.storage.objects) == [key]
        assert context.storage.objects[key]["content_type"] == "image/jpeg"

        deleted = await client.delete(PHOTO_URL, headers=headers)
        assert deleted.status_code == 204
        assert context.storage.objects == {}

        missing = await client.get(PHOTO_URL, headers=headers)
        assert missing.status_code == 404
        assert missing.json()["code"] == "photo_not_found"

        delete_again = await client.delete(PHOTO_URL, headers=headers)
        assert delete_again.status_code == 404


async def test_content_endpoint_redirects_to_presigned_url(make_context, client_factory, auth_headers):
    context = make_context()
    headers = auth_headers("user-1")

    async with client_factory(context) as client:
        await client.post(
            PHOTO_URL,
            headers=headers,
            files={"file": ("avatar.png", PNG, "image/png")},
        )

        response = await client.get(f"{PHOTO_URL}/content", headers=headers)

        assert response.status_code == 307
        assert response.headers["location"].startswith("https://b2.fake/users/user-1/photos/profile")
        assert "X-Amz-Expires=300" in response.headers["location"]


async def test_other_member_cannot_read_or_write(make_context, client_factory, auth_headers):
    context = make_context()
    owner = auth_headers("user-1")
    intruder = auth_headers("user-2")

    async with client_factory(context) as client:
        await client.post(PHOTO_URL, headers=owner, files={"file": ("a.png", PNG, "image/png")})

        assert (await client.get(PHOTO_URL, headers=intruder)).status_code == 403
        assert (
            await client.post(
                PHOTO_URL,
                headers=intruder,
                files={"file": ("b.png", PNG, "image/png")},
            )
        ).status_code == 403
        assert (await client.delete(PHOTO_URL, headers=intruder)).status_code == 403


async def test_admin_can_manage_any_user_photo(make_context, client_factory, auth_headers):
    context = make_context()
    admin = auth_headers("admin-1", "ADMIN")

    async with client_factory(context) as client:
        upload = await client.post(
            PHOTO_URL,
            headers=admin,
            files={"file": ("admin.png", PNG, "image/png")},
        )
        assert upload.status_code == 201
        assert (await client.get(PHOTO_URL, headers=admin)).status_code == 200


async def test_reviewer_can_read_but_not_write(make_context, client_factory, auth_headers):
    context = make_context()
    owner = auth_headers("user-1")
    reviewer = auth_headers("reviewer-1", "REVIEWER")

    async with client_factory(context) as client:
        await client.post(PHOTO_URL, headers=owner, files={"file": ("a.png", PNG, "image/png")})

        assert (await client.get(PHOTO_URL, headers=reviewer)).status_code == 200
        assert (
            await client.post(
                PHOTO_URL,
                headers=reviewer,
                files={"file": ("b.png", PNG, "image/png")},
            )
        ).status_code == 403
        assert (await client.delete(PHOTO_URL, headers=reviewer)).status_code == 403


async def test_rejects_invalid_type(make_context, client_factory, auth_headers):
    context = make_context()

    async with client_factory(context) as client:
        response = await client.post(
            PHOTO_URL,
            headers=auth_headers("user-1"),
            files={"file": ("nota.txt", b"hola mundo", "text/plain")},
        )

    assert response.status_code == 415
    assert response.json()["code"] == "invalid_file_type"
    assert context.storage.objects == {}


async def test_rejects_pdf_as_photo(make_context, client_factory, auth_headers):
    from tests.samples import PDF

    context = make_context()

    async with client_factory(context) as client:
        response = await client.post(
            PHOTO_URL,
            headers=auth_headers("user-1"),
            files={"file": ("doc.pdf", PDF, "application/pdf")},
        )

    assert response.status_code == 415


async def test_rejects_empty_file(make_context, client_factory, auth_headers):
    context = make_context()

    async with client_factory(context) as client:
        response = await client.post(
            PHOTO_URL,
            headers=auth_headers("user-1"),
            files={"file": ("vacia.png", b"", "image/png")},
        )

    assert response.status_code == 400
    assert response.json()["code"] == "empty_file"


async def test_rejects_oversized_photo(make_context, client_factory, auth_headers):
    context = make_context(max_photo_bytes=10)

    async with client_factory(context) as client:
        response = await client.post(
            PHOTO_URL,
            headers=auth_headers("user-1"),
            files={"file": ("grande.png", PNG, "image/png")},
        )

    assert response.status_code == 413
    assert response.json()["code"] == "file_too_large"
    assert context.storage.objects == {}


async def test_rejects_invalid_target_user_id(make_context, client_factory, auth_headers):
    context = make_context()

    async with client_factory(context) as client:
        response = await client.get(
            "/api/files/users/bad%20user/photo",
            headers=auth_headers("user-1"),
        )

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_user_id"


async def test_preserves_unicode_filename(make_context, client_factory, auth_headers):
    context = make_context()

    async with client_factory(context) as client:
        response = await client.post(
            PHOTO_URL,
            headers=auth_headers("user-1"),
            files={"file": ("fotografía.png", PNG, "image/png")},
        )

    assert response.status_code == 201
    assert response.json()["fileName"] == "fotografía.png"
