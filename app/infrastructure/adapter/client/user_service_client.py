"""Cliente opcional contra el user-microservice (solo consulta)."""

from __future__ import annotations

import asyncio
import time
from typing import Any
from urllib.parse import quote

import httpx

from app.config import Settings
from app.domain.exception.errors import ExternalServiceError, UserNotFoundError
from app.domain.port.out.user_client_port import UserClientPort


class DisabledUserClient(UserClientPort):
    """No-op: la validacion de existencia esta deshabilitada por defecto."""

    async def ensure_exists(self, user_id: str) -> None:
        return None

    async def aclose(self) -> None:
        return None


class UserServiceClient(UserClientPort):
    """Verifica usuarios usando una cuenta de servicio con rol ADMIN.

    ``GET /api/users/{id}`` del user-microservice exige ADMIN o REVIEWER, por
    eso se hace login con credenciales configuradas y se cachea el token.
    """

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.user_service_base_url.rstrip("/")
        self._email = settings.user_service_admin_email
        self._password = settings.user_service_admin_password
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=settings.user_service_timeout_seconds,
        )
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._lock = asyncio.Lock()

    async def _login(self) -> str:
        try:
            response = await self._client.post(
                "/api/auth/login",
                json={"email": self._email, "password": self._password},
            )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(
                f"No fue posible autenticarse contra user-microservice: {exc}"
            ) from exc

        if response.status_code != 200:
            raise ExternalServiceError(
                "Credenciales de servicio rechazadas por user-microservice "
                f"(HTTP {response.status_code})"
            )

        try:
            payload: dict[str, Any] = response.json()
            token = payload["accessToken"]
            expires_in = float(payload.get("expiresIn") or 900)
        except (ValueError, KeyError, TypeError) as exc:
            raise ExternalServiceError(
                "Respuesta de login invalida del user-microservice"
            ) from exc

        self._token = str(token)
        # Margen de 30s para no usar un token a punto de expirar.
        self._token_expires_at = time.monotonic() + max(expires_in - 30, 30)
        return self._token

    async def _get_token(self) -> str:
        if self._token and time.monotonic() < self._token_expires_at:
            return self._token
        async with self._lock:
            if self._token and time.monotonic() < self._token_expires_at:
                return self._token
            return await self._login()

    async def _fetch_user(self, user_id: str, token: str) -> httpx.Response:
        return await self._client.get(
            f"/api/users/{quote(user_id, safe='')}",
            headers={"Authorization": f"Bearer {token}"},
        )

    async def ensure_exists(self, user_id: str) -> None:
        token = await self._get_token()
        try:
            response = await self._fetch_user(user_id, token)
            if response.status_code == 401:
                # Token revocado/expirado: renovar una sola vez.
                async with self._lock:
                    self._token = None
                token = await self._get_token()
                response = await self._fetch_user(user_id, token)
        except httpx.HTTPError as exc:
            raise ExternalServiceError(
                f"No fue posible consultar el usuario en user-microservice: {exc}"
            ) from exc

        if response.status_code == 404:
            raise UserNotFoundError(user_id)
        if response.status_code in (401, 403):
            raise ExternalServiceError(
                "La cuenta de servicio no tiene permisos para consultar usuarios "
                "(se requiere rol ADMIN o REVIEWER)"
            )
        if response.status_code >= 400:
            raise ExternalServiceError(
                f"user-microservice respondio HTTP {response.status_code} al consultar el usuario"
            )

    async def aclose(self) -> None:
        await self._client.aclose()
