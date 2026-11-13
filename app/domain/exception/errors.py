"""Excepciones del dominio y de la aplicacion."""

from __future__ import annotations


class DomainError(Exception):
    """Excepcion base para errores de negocio esperados."""

    code = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ValidationError(DomainError):
    code = "validation_error"


class EmptyFileError(ValidationError):
    code = "empty_file"

    def __init__(self) -> None:
        super().__init__("El archivo esta vacio")


class FileTooLargeError(ValidationError):
    code = "file_too_large"

    def __init__(self, max_bytes: int, kind: str) -> None:
        self.max_bytes = max_bytes
        super().__init__(
            f"El archivo supera el tamano maximo permitido para {kind} "
            f"({max_bytes} bytes)"
        )


class InvalidFileTypeError(ValidationError):
    code = "invalid_file_type"

    def __init__(self, allowed: str) -> None:
        self.allowed = allowed
        super().__init__(f"Tipo de archivo no permitido. Formatos aceptados: {allowed}")


class InvalidUserIdError(ValidationError):
    code = "invalid_user_id"

    def __init__(self, value: str) -> None:
        super().__init__(
            f"Identificador de usuario invalido: {value!r}. "
            "Solo se permiten letras, numeros, punto, guion y guion bajo (1-64)."
        )


class InvalidDocumentIdError(ValidationError):
    code = "invalid_document_id"

    def __init__(self, value: str) -> None:
        super().__init__(
            f"Identificador de documento invalido: {value!r}. Se esperan 32 "
            "caracteres hexadecimales."
        )


class NotFoundError(DomainError):
    code = "not_found"


class PhotoNotFoundError(NotFoundError):
    code = "photo_not_found"

    def __init__(self) -> None:
        super().__init__("El usuario no tiene una foto registrada")


class DocumentNotFoundError(NotFoundError):
    code = "document_not_found"

    def __init__(self, document_id: str) -> None:
        self.document_id = document_id
        super().__init__(f"Documento no encontrado: {document_id}")


class ForbiddenError(DomainError):
    code = "forbidden"

    def __init__(self, message: str = "No tiene permisos para realizar esta operacion") -> None:
        super().__init__(message)


class UserNotFoundError(NotFoundError):
    code = "user_not_found"

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        super().__init__(f"El usuario {user_id!r} no existe")


class ExternalServiceError(DomainError):
    code = "external_service_error"

    def __init__(self, message: str = "Servicio externo no disponible") -> None:
        super().__init__(message)


class StorageError(DomainError):
    code = "storage_error"

    def __init__(self, message: str = "No fue posible comunicarse con el almacenamiento") -> None:
        super().__init__(message)
