"""Punto de entrada de la aplicacion FastAPI."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.domain.port.out.file_storage_port import FileStoragePort
from app.domain.port.out.user_client_port import UserClientPort
from app.entrypoint.rest.errors import register_exception_handlers
from app.entrypoint.rest.routers import documents, files, health, photos
from app.infrastructure.config.container import build_container

logger = logging.getLogger(__name__)

_DESCRIPTION = """
Microservicio de archivos con arquitectura hexagonal.

* **Fotos**: una sola foto de perfil por usuario (JPEG, PNG o WebP).
* **Documentos**: multiples PDF por usuario.
* **Sin base de datos**: los metadatos viven como metadata del objeto en Backblaze B2.
* **Autenticacion**: JWT HS256 emitido por el `user-microservice` (mismo `JWT_SECRET`).
* **Descargas**: URLs prefirmadas de corta duracion (bucket privado).

Permisos: el dueño o un `ADMIN` pueden escribir; el dueño, un `ADMIN` o un
`REVIEWER` pueden leer.
"""


def create_app(
    settings: Settings | None = None,
    storage: FileStoragePort | None = None,
    user_client: UserClientPort | None = None,
) -> FastAPI:
    """Fabrica de la aplicacion. Permite inyectar fakes en tests."""

    resolved_settings = settings or get_settings()
    container = build_container(
        resolved_settings,
        storage=storage,
        user_client=user_client,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        logger.info(
            "Iniciando %s (env=%s, bucket=%s)",
            resolved_settings.app_name,
            resolved_settings.environment,
            resolved_settings.b2_bucket_name,
        )
        try:
            yield
        finally:
            await container.aclose()

    app = FastAPI(
        title="File Microservice",
        version=resolved_settings.app_version,
        description=_DESCRIPTION,
        lifespan=lifespan,
        openapi_tags=[
            {"name": "health", "description": "Estado del servicio (no consulta B2)."},
            {"name": "photos", "description": "Foto de perfil unica por usuario."},
            {"name": "documents", "description": "Documentos PDF multiples."},
            {"name": "files", "description": "Operaciones sobre todos los archivos del usuario."},
        ],
    )
    app.state.settings = resolved_settings
    app.state.container = container

    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origin_list,
        allow_credentials=resolved_settings.cors_origin_list != ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )

    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(photos.router)
    app.include_router(documents.router)
    app.include_router(files.router)
    return app


app = create_app()
