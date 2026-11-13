"""Endpoints de documentos PDF (multiples por usuario)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from fastapi.responses import RedirectResponse

from app.domain.model.actor import Actor
from app.domain.valueobject.file_category import FileCategory
from app.entrypoint.rest.auth import get_current_actor
from app.entrypoint.rest.dependencies import get_container
from app.entrypoint.rest.mapper import to_document_response
from app.entrypoint.rest.schemas import DocumentListResponse, DocumentResponse
from app.entrypoint.rest.uploads import read_upload
from app.infrastructure.config.container import ServiceContainer

router = APIRouter(prefix="/api/files/users/{user_id}", tags=["documents"])


@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir un documento PDF",
)
async def upload_document(
    user_id: str,
    file: UploadFile = File(..., description="Documento PDF"),
    actor: Actor = Depends(get_current_actor),
    container: ServiceContainer = Depends(get_container),
) -> DocumentResponse:
    upload = await read_upload(
        file,
        max_bytes=container.settings.max_document_bytes,
        category=FileCategory.DOCUMENT,
    )
    result = await container.document_service.upload(actor, user_id, upload)
    return to_document_response(result)


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="Listar documentos del usuario (paginado)",
)
async def list_documents(
    user_id: str,
    limit: int | None = Query(default=None, ge=1, le=1000),
    cursor: str | None = Query(default=None, description="Cursor opaco de la pagina anterior"),
    actor: Actor = Depends(get_current_actor),
    container: ServiceContainer = Depends(get_container),
) -> DocumentListResponse:
    effective_limit = limit or container.settings.default_list_limit
    page = await container.document_service.list(actor, user_id, effective_limit, cursor)
    return DocumentListResponse(
        items=[to_document_response(item) for item in page.items],
        next_cursor=page.next_cursor,
    )


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="Obtener metadatos y URL temporal de un documento",
)
async def get_document(
    user_id: str,
    document_id: str,
    actor: Actor = Depends(get_current_actor),
    container: ServiceContainer = Depends(get_container),
) -> DocumentResponse:
    result = await container.document_service.get(actor, user_id, document_id)
    return to_document_response(result)


@router.get(
    "/documents/{document_id}/content",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    summary="Descargar un documento (redireccion a URL firmada)",
    responses={307: {"description": "Redireccion a Backblaze B2"}},
)
async def download_document(
    user_id: str,
    document_id: str,
    actor: Actor = Depends(get_current_actor),
    container: ServiceContainer = Depends(get_container),
) -> RedirectResponse:
    result = await container.document_service.get(actor, user_id, document_id)
    return RedirectResponse(url=result.download_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un documento",
)
async def delete_document(
    user_id: str,
    document_id: str,
    actor: Actor = Depends(get_current_actor),
    container: ServiceContainer = Depends(get_container),
) -> Response:
    await container.document_service.delete(actor, user_id, document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
