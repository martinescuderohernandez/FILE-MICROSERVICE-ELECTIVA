"""Manejo uniforme de errores HTTP."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.exception.errors import (
    DomainError,
    ExternalServiceError,
    FileTooLargeError,
    ForbiddenError,
    InvalidFileTypeError,
    NotFoundError,
    StorageError,
    ValidationError,
)


def _status_for(error: DomainError) -> int:
    if isinstance(error, FileTooLargeError):
        return status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    if isinstance(error, InvalidFileTypeError):
        return status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    if isinstance(error, ForbiddenError):
        return status.HTTP_403_FORBIDDEN
    if isinstance(error, NotFoundError):
        return status.HTTP_404_NOT_FOUND
    if isinstance(error, StorageError):
        return status.HTTP_502_BAD_GATEWAY
    if isinstance(error, ExternalServiceError):
        return status.HTTP_503_SERVICE_UNAVAILABLE
    if isinstance(error, ValidationError):
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_400_BAD_REQUEST


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=_status_for(exc),
            content={"detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": jsonable_encoder(exc.errors()),
                "code": "request_validation_error",
            },
        )
