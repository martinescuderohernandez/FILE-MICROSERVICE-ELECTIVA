"""Puerto de salida para verificar usuarios en el user-microservice."""

from __future__ import annotations

from abc import ABC, abstractmethod


class UserClientPort(ABC):
    """Verificacion opcional de existencia de un usuario.

    El file-microservice no persiste usuarios ni modifica el user-microservice;
    solo puede consultar su API si la integracion esta habilitada.
    """

    @abstractmethod
    async def ensure_exists(self, user_id: str) -> None:
        """Lanza ``UserNotFoundError`` si el usuario no existe."""

    async def aclose(self) -> None:
        return None
