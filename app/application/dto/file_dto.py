"""DTOs de la capa de aplicacion.

Los DTOs reutilizan las estructuras inmutables del dominio para no duplicar
contratos entre capas.
"""

from app.domain.model.file_operations import DocumentPage, FileResult, UploadedFile

__all__ = ["DocumentPage", "FileResult", "UploadedFile"]
