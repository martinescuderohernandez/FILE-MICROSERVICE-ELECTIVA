"""Endpoints de administracion de archivos de un usuario."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.domain.model.actor import Actor
from app.entrypoint.rest.auth import get_current_actor
from app.entrypoint.rest.dependencies import get_container
from app.entrypoint.rest.schemas import DeleteAllResponse
from app.infrastructure.config.container import ServiceContainer

router = APIRouter(prefix="/api/files/users/{user_id}", tags=["files"])


@router.delete(
    "/files",
    response_model=DeleteAllResponse,
    status_code=status.HTTP_200_OK,
    summary="Eliminar foto y documentos del usuario",
)
async def delete_all_files(
    user_id: str,
    actor: Actor = Depends(get_current_actor),
    container: ServiceContainer = Depends(get_container),
) -> DeleteAllResponse:
    deleted = await container.user_files_service.delete_all(actor, user_id)
    return DeleteAllResponse(deleted_count=deleted)
