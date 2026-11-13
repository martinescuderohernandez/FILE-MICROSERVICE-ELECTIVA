"""Tests de documentos PDF multiples."""

from __future__ import annotations

import re

from tests.samples import PDF, PNG

DOCS_URL = "/api/files/users/user-1/documents"
DOC_ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")


async def _upload(client, headers, name: str = "documento.pdf"):
    return await client.post(
        DOCS_URL,
        headers=headers,
        files={"file": (name, PDF, "application/pdf")},
    )


async def test_upload_list_get_download_and_delete_document(
    make_context, client_factory, auth_headers
):
    context = make_context()
    headers = auth_headers("user-1")

    async with client_factory(context) as client:
        upload = await _upload(client, headers, "trabajo.pdf")
        assert upload.status_code == 201, upload.text
        body = upload.json()
        document_id = body["documentId"]
        assert DOC_ID_PATTERN.fullmatch(document_id)
        assert body["fileName"] == "trabajo.pdf"
        assert body["contentType"] == "application/pdf"
        assert body["downloadUrl"].startswith("https://b2.fake/")

        key = f"users/user-1/documents/{document_id}.pdf"
        assert list(context.storage.objects) == [key]

        listed = await client.get(DOCS_URL, headers=headers)
        assert listed.status_code == 200
        page = listed.json()
        assert len(page["items"]) == 1
        assert page["items"][0]["documentId"] == document_id
        assert page["nextCursor"] is None

        detail = await client.get(f"{DOCS_URL}/{document_id}", headers=headers)
        assert detail.status_code == 200
        assert detail.json()["fileName"] == "trabajo.pdf"

        download = await client.get(f"{DOCS_URL}/{document_id}/content", headers=headers)
        assert download.status_code == 307
        assert download.headers["location"] == body["downloadUrl"]

        deleted = await client.delete(f"{DOCS_URL}/{document_id}", headers=headers)
        assert deleted.status_code == 204
        assert context.storage.objects == {}

        missing = await client.get(f"{DOCS_URL}/{document_id}", headers=headers)
        assert missing.status_code == 404
        assert missing.json()["code"] == "document_not_found"


async def test_multiple_documents_are_independent(make_context, client_factory, auth_headers):
    context = make_context()
    headers = auth_headers("user-1")

    async with client_factory(context) as client:
        first = await _upload(client, headers, "uno.pdf")
        second = await _upload(client, headers, "dos.pdf")

        assert first.status_code == 201
        assert second.status_code == 201
        assert first.json()["documentId"] != second.json()["documentId"]
        assert len(context.storage.objects) == 2


async def test_pagination_walks_all_documents(make_context, client_factory, auth_headers):
    context = make_context()
    headers = auth_headers("user-1")

    async with client_factory(context) as client:
        for name in ("a.pdf", "b.pdf", "c.pdf"):
            assert (await _upload(client, headers, name)).status_code == 201

        first = await client.get(DOCS_URL, headers=headers, params={"limit": 2})
        assert first.status_code == 200
        first_page = first.json()
        assert len(first_page["items"]) == 2
        assert first_page["nextCursor"]

        second = await client.get(
            DOCS_URL,
            headers=headers,
            params={"limit": 2, "cursor": first_page["nextCursor"]},
        )
        assert second.status_code == 200
        second_page = second.json()
        assert len(second_page["items"]) == 1
        assert second_page["nextCursor"] is None

        names = [item["fileName"] for item in first_page["items"] + second_page["items"]]
        assert sorted(names) == ["a.pdf", "b.pdf", "c.pdf"]


async def test_rejects_non_pdf_document(make_context, client_factory, auth_headers):
    context = make_context()

    async with client_factory(context) as client:
        response = await client.post(
            DOCS_URL,
            headers=auth_headers("user-1"),
            files={"file": ("foto.png", PNG, "image/png")},
        )

    assert response.status_code == 415
    assert context.storage.objects == {}


async def test_rejects_invalid_document_id(make_context, client_factory, auth_headers):
    context = make_context()

    async with client_factory(context) as client:
        response = await client.get(f"{DOCS_URL}/no-es-un-id", headers=auth_headers("user-1"))

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_document_id"


async def test_document_id_traversal_is_rejected(make_context, client_factory, auth_headers):
    context = make_context()

    async with client_factory(context) as client:
        response = await client.get(f"{DOCS_URL}/..%2F..%2Fphoto", headers=auth_headers("user-1"))

    assert response.status_code in (400, 404)
    assert context.storage.objects == {}


async def test_other_member_cannot_list_or_delete_documents(
    make_context, client_factory, auth_headers
):
    context = make_context()
    owner = auth_headers("user-1")
    intruder = auth_headers("user-2")

    async with client_factory(context) as client:
        created = await _upload(client, owner)
        document_id = created.json()["documentId"]

        assert (await client.get(DOCS_URL, headers=intruder)).status_code == 403
        assert (await client.get(f"{DOCS_URL}/{document_id}", headers=intruder)).status_code == 403
        assert (await client.delete(f"{DOCS_URL}/{document_id}", headers=intruder)).status_code == 403


async def test_reviewer_can_list_documents(make_context, client_factory, auth_headers):
    context = make_context()
    owner = auth_headers("user-1")
    reviewer = auth_headers("reviewer-1", "REVIEWER")

    async with client_factory(context) as client:
        await _upload(client, owner, "revisable.pdf")

        response = await client.get(DOCS_URL, headers=reviewer)

    assert response.status_code == 200
    assert response.json()["items"][0]["fileName"] == "revisable.pdf"


async def test_sanitizes_filename_with_path(make_context, client_factory, auth_headers):
    context = make_context()

    async with client_factory(context) as client:
        response = await _upload(client, auth_headers("user-1"), "../../etc/passwd.pdf")

    assert response.status_code == 201
    assert response.json()["fileName"] == "passwd.pdf"
