"""Configuracion central del microservicio basada en variables de entorno."""

from __future__ import annotations

import base64
import binascii
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Secreto de desarrollo del user-microservice. Sirve para levantar el proyecto
# localmente sin configuracion adicional, pero DEBE reemplazarse en produccion.
DEV_JWT_SECRET = "ZGV2ZWxvcG1lbnQtb25seS1qd3Qtc2VjcmV0LW11c3QtYmUtcmVwbGFjZWQ="


def decode_jwt_secret(secret: str) -> bytes:
    """Decodifica el secreto igual que Spring Boot.

    Java usa ``Keys.hmacShaKeyFor(Base64.getDecoder().decode(secret))``.
    El decoder de Java acepta Base64 sin padding, por eso se agrega antes de
    decodificar. Un secreto invalido o de menos de 32 bytes es un error fatal.
    """

    candidate = secret.strip()
    if not candidate:
        raise ValueError("JWT_SECRET no puede estar vacio")

    padded = candidate + "=" * (-len(candidate) % 4)
    try:
        key = base64.b64decode(padded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("JWT_SECRET debe estar codificado en Base64") from exc

    if len(key) < 32:
        raise ValueError(
            "JWT_SECRET debe decodificar a al menos 32 bytes para HS256 "
            f"(actual: {len(key)} bytes)"
        )
    return key


class Settings(BaseSettings):
    """Configuracion de la aplicacion leida desde entorno o archivo .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "file-microservice"
    app_version: str = "1.0.0"
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8001
    log_level: str = "info"

    # --- Seguridad / JWT compartido con user-microservice ---
    jwt_secret: str = DEV_JWT_SECRET
    jwt_algorithm: str = "HS256"

    # --- Backblaze B2 (S3 compatible) ---
    b2_key_id: str = ""
    b2_application_key: str = ""
    b2_bucket_name: str = "certificados-lab-dev-2026"
    b2_endpoint_url: str = "https://s3.us-east-005.backblazeb2.com"
    b2_region: str = "us-east-005"

    # --- Limites / paginacion / URLs firmadas ---
    max_photo_bytes: int = Field(default=5 * 1024 * 1024, gt=0)
    max_document_bytes: int = Field(default=20 * 1024 * 1024, gt=0)
    presigned_url_ttl_seconds: int = Field(default=300, gt=0, le=604800)
    max_list_limit: int = Field(default=100, ge=1, le=1000)
    default_list_limit: int = Field(default=20, ge=1, le=100)

    # --- CORS ---
    cors_origins: str = "*"

    # --- Verificacion opcional contra user-microservice ---
    user_service_enabled: bool = False
    user_service_base_url: str = "http://localhost:8080"
    user_service_admin_email: str = ""
    user_service_admin_password: str = ""
    user_service_timeout_seconds: float = Field(default=5.0, gt=0)

    @field_validator("jwt_algorithm")
    @classmethod
    def _validate_algorithm(cls, value: str) -> str:
        if value.upper() != "HS256":
            raise ValueError("Solo se soporta HS256 para compartir tokens con user-microservice")
        return "HS256"

    @field_validator("b2_endpoint_url")
    @classmethod
    def _normalize_endpoint(cls, value: str) -> str:
        return value.rstrip("/")

    @field_validator("b2_region", "b2_bucket_name")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("El valor no puede estar vacio")
        return value.strip()

    @field_validator("jwt_secret")
    @classmethod
    def _validate_jwt_secret(cls, value: str) -> str:
        decode_jwt_secret(value)
        return value

    @field_validator("default_list_limit")
    @classmethod
    def _clamp_default_limit(cls, value: int, info) -> int:
        max_limit = info.data.get("max_list_limit", 100)
        return min(value, max_limit)

    @property
    def jwt_key(self) -> bytes:
        """Clave HMAC lista para PyJWT."""
        return decode_jwt_secret(self.jwt_secret)

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return origins or ["*"]

    @property
    def b2_credentials_configured(self) -> bool:
        return bool(self.b2_key_id and self.b2_application_key)

    @property
    def user_service_credentials_configured(self) -> bool:
        return bool(self.user_service_admin_email and self.user_service_admin_password)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelve la configuracion singleton (cacheada)."""
    return Settings()
