"""Puerto de salida para el almacenamiento de objetos."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Mapping

from app.domain.model.file_page import FilePage
from app.domain.model.stored_file import StoredFile


class FileStoragePort(ABC):
    """Contrato que debe implementar cualquier proveedor de objetos.

    La implementacion concreta (Backblaze B2) vive en infraestructura.
    Los metodos son asincronos para no bloquear el event loop de FastAPI.
    """

    @abstractmethod
    async def put(
        self,
        key: str,
        data: bytes,
        content_type: str,
        metadata: Mapping[str, str] | None = None,
    ) -> StoredFile:
        """Crea o reemplaza un objeto."""

    @abstractmethod
    async def head(self, key: str) -> StoredFile | None:
        """Devuelve metadatos del objeto o ``None`` si no existe."""

    @abstractmethod
    async def list(
        self,
        prefix: str,
        cursor: str | None = None,
        limit: int = 100,
    ) -> FilePage:
        """Lista objetos bajo un prefijo de forma paginada."""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Elimina un objeto. Devuelve ``True`` si existia."""

    @abstractmethod
    async def delete_prefix(self, prefix: str) -> int:
        """Elimina todos los objetos bajo un prefijo y devuelve el total."""

    @abstractmethod
    async def presigned_get_url(self, key: str, expires_in: int) -> str:
        """Genera una URL temporal de descarga para un objeto privado."""

    async def aclose(self) -> None:
        """Libera recursos del cliente. Opcional para implementaciones fake."""
        return None
