"""Contenedor de dependencias y cableado de casos de uso."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.service.document_service import DocumentService
from app.application.service.file_validator import FileValidator
from app.application.service.photo_service import PhotoService
from app.application.service.user_files_service import UserFilesService
from app.config import Settings
from app.domain.port.out.file_storage_port import FileStoragePort
from app.domain.port.out.user_client_port import UserClientPort
from app.infrastructure.adapter.client.user_service_client import (
    DisabledUserClient,
    UserServiceClient,
)
from app.infrastructure.adapter.storage.b2_storage_adapter import B2StorageAdapter


@dataclass(slots=True)
class ServiceContainer:
    """Instancias compartidas por los routers."""

    settings: Settings
    storage: FileStoragePort
    user_client: UserClientPort
    photo_service: PhotoService
    document_service: DocumentService
    user_files_service: UserFilesService

    async def aclose(self) -> None:
        await self.storage.aclose()
        await self.user_client.aclose()


def build_user_client(settings: Settings) -> UserClientPort:
    if not settings.user_service_enabled:
        return DisabledUserClient()
    if not settings.user_service_credentials_configured:
        raise ValueError(
            "USER_SERVICE_ENABLED=true requiere USER_SERVICE_ADMIN_EMAIL y "
            "USER_SERVICE_ADMIN_PASSWORD (cuenta con rol ADMIN)"
        )
    return UserServiceClient(settings)


def build_container(
    settings: Settings,
    storage: FileStoragePort | None = None,
    user_client: UserClientPort | None = None,
) -> ServiceContainer:
    """Cablea adaptadores y servicios. Los tests inyectan fakes aqui."""

    resolved_storage = storage or B2StorageAdapter(settings)
    resolved_user_client = user_client or build_user_client(settings)

    validator = FileValidator(
        max_photo_bytes=settings.max_photo_bytes,
        max_document_bytes=settings.max_document_bytes,
    )

    return ServiceContainer(
        settings=settings,
        storage=resolved_storage,
        user_client=resolved_user_client,
        photo_service=PhotoService(
            storage=resolved_storage,
            validator=validator,
            user_client=resolved_user_client,
            presigned_ttl_seconds=settings.presigned_url_ttl_seconds,
        ),
        document_service=DocumentService(
            storage=resolved_storage,
            validator=validator,
            user_client=resolved_user_client,
            presigned_ttl_seconds=settings.presigned_url_ttl_seconds,
            max_list_limit=settings.max_list_limit,
        ),
        user_files_service=UserFilesService(storage=resolved_storage),
    )
