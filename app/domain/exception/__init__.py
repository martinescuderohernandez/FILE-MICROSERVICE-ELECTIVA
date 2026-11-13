"""Excepciones de dominio."""

from app.domain.exception.errors import (
    DocumentNotFoundError,
    DomainError,
    EmptyFileError,
    ExternalServiceError,
    FileTooLargeError,
    ForbiddenError,
    InvalidDocumentIdError,
    InvalidFileTypeError,
    InvalidUserIdError,
    NotFoundError,
    PhotoNotFoundError,
    StorageError,
    UserNotFoundError,
    ValidationError,
)

__all__ = [
    "DocumentNotFoundError",
    "DomainError",
    "EmptyFileError",
    "ExternalServiceError",
    "FileTooLargeError",
    "ForbiddenError",
    "InvalidDocumentIdError",
    "InvalidFileTypeError",
    "InvalidUserIdError",
    "NotFoundError",
    "PhotoNotFoundError",
    "StorageError",
    "UserNotFoundError",
    "ValidationError",
]
