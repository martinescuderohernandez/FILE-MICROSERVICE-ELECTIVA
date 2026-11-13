"""Construccion de claves S3 a partir de los objetos de valor del dominio."""

from __future__ import annotations

from app.domain.exception.errors import InvalidDocumentIdError
from app.domain.valueobject.document_id import DocumentId
from app.domain.valueobject.user_id import UserId


class ObjectKeyFactory:
    """Centraliza el layout de objetos en el bucket.

    Layout:
        users/{user_id}/photos/profile                     (foto unica)
        users/{user_id}/documents/{document_id}.pdf        (N documentos)
        users/{user_id}/                                    (todo el usuario)
    """

    @staticmethod
    def user_prefix(user_id: str) -> str:
        return f"users/{UserId(user_id).value}/"

    @staticmethod
    def photo_key(user_id: str) -> str:
        return f"users/{UserId(user_id).value}/photos/profile"

    @staticmethod
    def photo_prefix(user_id: str) -> str:
        return f"users/{UserId(user_id).value}/photos/"

    @staticmethod
    def document_prefix(user_id: str) -> str:
        return f"users/{UserId(user_id).value}/documents/"

    @staticmethod
    def document_key(user_id: str, document_id: str) -> str:
        return (
            f"users/{UserId(user_id).value}/documents/"
            f"{DocumentId(document_id).value}.pdf"
        )

    @staticmethod
    def document_id_from_key(key: str) -> str | None:
        """Extrae el id desde ``.../documents/<id>.pdf`` sin lanzar excepcion."""

        name = key.rsplit("/", 1)[-1]
        if not name.endswith(".pdf"):
            return None
        candidate = name[: -len(".pdf")]
        try:
            return DocumentId(candidate).value
        except InvalidDocumentIdError:
            return None
