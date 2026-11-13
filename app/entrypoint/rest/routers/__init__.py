"""Endpoints HTTP."""

from app.entrypoint.rest.routers import documents, files, health, photos

__all__ = ["documents", "files", "health", "photos"]
