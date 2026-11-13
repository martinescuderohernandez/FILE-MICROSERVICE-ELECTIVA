"""Router de salud. No consulta B2 para no consumir transacciones."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import Settings
from app.entrypoint.rest.dependencies import get_app_settings
from app.entrypoint.rest.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Estado del servicio")
async def health(settings: Settings = Depends(get_app_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {
        "service": "file-microservice",
        "docs": "/docs",
        "health": "/health",
    }
