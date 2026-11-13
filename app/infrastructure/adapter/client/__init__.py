"""Clientes de servicios externos."""

from app.infrastructure.adapter.client.user_service_client import (
    DisabledUserClient,
    UserServiceClient,
)

__all__ = ["DisabledUserClient", "UserServiceClient"]
