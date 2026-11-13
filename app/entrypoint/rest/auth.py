"""Autenticacion JWT compatible con el user-microservice (HS256)."""

from __future__ import annotations

import logging

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings
from app.domain.exception.errors import InvalidUserIdError
from app.domain.model.actor import Actor, Role
from app.domain.valueobject.user_id import UserId

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False, description="JWT emitido por user-microservice")


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def decode_access_token(token: str, settings: Settings) -> Actor:
    """Valida firma/exp del JWT y construye el actor autenticado.

    El user-microservice firma con ``sub`` (id del usuario) y ``role``. La clave
    es el JWT_SECRET compartido, decodificado desde Base64 igual que Spring.
    """

    try:
        payload = jwt.decode(
            token,
            settings.jwt_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub"], "verify_signature": True},
        )
    except jwt.ExpiredSignatureError as exc:
        raise _unauthorized("El token expiro") from exc
    except jwt.PyJWTError as exc:
        logger.info("Token JWT rechazado: %s", exc)
        raise _unauthorized("Token invalido") from exc

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise _unauthorized("El token no contiene el sujeto (sub)")

    try:
        user_id = UserId(subject).value
        role = Role.from_claim(payload.get("role"))
    except (InvalidUserIdError, ValueError) as exc:
        raise _unauthorized(f"Claims invalidos en el token: {exc}") from exc

    return Actor(user_id=user_id, role=role)


async def get_current_actor(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> Actor:
    if credentials is None or not credentials.credentials:
        raise _unauthorized("Se requiere un Bearer token")
    settings: Settings = request.app.state.settings
    return decode_access_token(credentials.credentials, settings)
