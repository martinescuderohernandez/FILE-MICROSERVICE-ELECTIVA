"""Endpoints de la foto de perfil (una por usuario)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from fastapi.responses import RedirectResponse

from app.domain.model.actor import Actor
from app.domain.valueobject.file_category import FileCategory
from app.entrypoint.rest.auth import get_current_actor
from app.entrypoint.rest.dependencies import get_container
from app.entrypoint.rest.mapper import to_photo_response
from app.entrypoint.rest.schemas import PhotoResponse
from app.entrypoint.rest.uploads import read_upload
from app.infrastructure.config.container import ServiceContainer

router = APIRouter(prefix="/api/files/users/{user_id}", tags=["photos"])


@router.post(
    "/photo",
    response_model=PhotoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir o reemplazar la foto del usuario",
)
async def upload_photo(
    user_id: str,
    file: UploadFile = File(..., description="JPEG, PNG o WebP"),
    actor: Actor = Depends(get_current_actor),
    container: ServiceContainer = Depends(get_container),
) -> PhotoResponse:
    upload = await read_upload(
        file,
        max_bytes=container.settings.max_photo_bytes,
        category=FileCategory.PHOTO,
    )
    result = await container.photo_service.upload(actor, user_id, upload)
    return to_photo_response(result)


@router.get(
    "/photo",
    response_model=PhotoResponse,
    summary="Obtener metadatos y URL temporal de la foto",
)
async def get_photo(
    user_id: str,
    actor: Actor = Depends(get_current_actor),
    container: ServiceContainer = Depends(get_container),
) -> PhotoResponse:
    result = await container.photo_service.get(actor, user_id)
    return to_photo_response(result)


@router.get(
    "/photo/content",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    summary="Descargar la foto (redireccion a URL firmada)",
    responses={307: {"description": "Redireccion a Backblaze B2"}},
)
async def download_photo(
    user_id: str,
    actor: Actor = Depends(get_current_actor),
    container: ServiceContainer = Depends(get_container),
) -> RedirectResponse:
    result = await container.photo_service.get(actor, user_id)
    return RedirectResponse(url=result.download_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.delete(
    "/photo",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar la foto del usuario",
)
async def delete_photo(
    user_id: str,
    actor: Actor = Depends(get_current_actor),
    container: ServiceContainer = Depends(get_container),
) -> Response:
    await container.photo_service.delete(actor, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
