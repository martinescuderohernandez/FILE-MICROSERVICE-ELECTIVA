"""Tests unitarios de validacion y claves de objeto."""

from __future__ import annotations

import pytest

from app.application.service.file_validator import FileValidator, sanitize_filename
from app.application.service.object_key_factory import ObjectKeyFactory
from app.domain.exception.errors import EmptyFileError, FileTooLargeError, InvalidFileTypeError
from app.domain.valueobject.document_id import DocumentId
from app.domain.valueobject.user_id import UserId
from tests.samples import JPEG, PDF, PNG


def test_validate_photo_accepts_supported_formats():
    validator = FileValidator(1024, 1024)

    assert validator.validate_photo(PNG).content_type == "image/png"
    assert validator.validate_photo(JPEG).content_type == "image/jpeg"


def test_validate_document_accepts_pdf():
    validator = FileValidator(1024, 1024)

    validated = validator.validate_document(PDF)

    assert validated.content_type == "application/pdf"
    assert validated.extension == "pdf"


def test_validate_rejects_text():
    validator = FileValidator(1024, 1024)

    with pytest.raises(InvalidFileTypeError):
        validator.validate_photo(b"contenido plano")
    with pytest.raises(InvalidFileTypeError):
        validator.validate_document(b"contenido plano")


def test_validate_rejects_empty_and_oversized():
    validator = FileValidator(10, 10)

    with pytest.raises(EmptyFileError):
        validator.validate_photo(b"")
    with pytest.raises(FileTooLargeError):
        validator.validate_photo(PNG)


def test_sanitize_filename_strips_paths_and_control_chars():
    assert sanitize_filename("../../etc/passwd.pdf", "document.pdf") == "passwd.pdf"
    assert sanitize_filename("carpeta\\foto.png", "photo.png") == "foto.png"
    assert sanitize_filename("ma\x00l.png", "photo.png") == "mal.png"
    assert sanitize_filename("", "photo.png") == "photo.png"
    assert sanitize_filename(None, "photo.png") == "photo.png"


def test_object_key_layout():
    keys = ObjectKeyFactory()

    assert keys.photo_key("user-1") == "users/user-1/photos/profile"
    assert keys.document_prefix("user-1") == "users/user-1/documents/"
    assert keys.user_prefix("user-1") == "users/user-1/"
    document_id = "a" * 32
    assert keys.document_key("user-1", document_id) == f"users/user-1/documents/{document_id}.pdf"
    assert keys.document_id_from_key(f"users/user-1/documents/{document_id}.pdf") == document_id
    assert keys.document_id_from_key("users/user-1/documents/no-valido.pdf") is None


def test_value_objects_reject_injection():
    with pytest.raises(Exception):
        UserId("../admin")
    with pytest.raises(Exception):
        UserId("")
    with pytest.raises(Exception):
        UserId("..")
    with pytest.raises(Exception):
        UserId(".")
    with pytest.raises(Exception):
        DocumentId("../../etc/passwd")
    with pytest.raises(Exception):
        DocumentId("A" * 32)
