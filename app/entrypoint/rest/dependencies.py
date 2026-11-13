"""Dependencias compartidas por los routers."""

from __future__ import annotations

from fastapi import Request

from app.config import Settings
from app.infrastructure.config.container import ServiceContainer


def get_container(request: Request) -> ServiceContainer:
    return request.app.state.container


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings
