"""Contratos de los casos de uso de archivos."""

from __future__ import annotations

from typing import Optional, Protocol

from app.domain.model.actor import Actor
from app.domain.model.file_operations import DocumentPage, FileResult, UploadedFile


class UploadPhotoUseCase(Protocol):
    async def upload(self, actor: Actor, user_id: str, upload: UploadedFile) -> FileResult:
        ...


class GetPhotoUseCase(Protocol):
    async def get(self, actor: Actor, user_id: str) -> FileResult:
        ...


class DeletePhotoUseCase(Protocol):
    async def delete(self, actor: Actor, user_id: str) -> None:
        ...


class UploadDocumentUseCase(Protocol):
    async def upload(self, actor: Actor, user_id: str, upload: UploadedFile) -> FileResult:
        ...


class ListDocumentsUseCase(Protocol):
    async def list(
        self,
        actor: Actor,
        user_id: str,
        limit: int,
        cursor: Optional[str] = None,
    ) -> DocumentPage:
        ...


class GetDocumentUseCase(Protocol):
    async def get(self, actor: Actor, user_id: str, document_id: str) -> FileResult:
        ...


class DeleteDocumentUseCase(Protocol):
    async def delete(self, actor: Actor, user_id: str, document_id: str) -> None:
        ...


class DeleteAllFilesUseCase(Protocol):
    async def delete_all(self, actor: Actor, user_id: str) -> int:
        ...
