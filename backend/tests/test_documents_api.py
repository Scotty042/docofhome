from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.db.session import get_session
from app.main import app
from app.schemas.documents import (
    DocumentDownload,
    DocumentEntry,
    DocumentEntryType,
    DocumentListRead,
    DocumentMutationRead,
)
from app.services.documents import (
    DocumentConflictError,
    DocumentService,
    DocumentTooLargeError,
)


@pytest.fixture
def documents_client(tmp_path: Path) -> Generator[TestClient]:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'documents-api.sqlite3'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)

    def override_session() -> Generator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def sample_entry(name: str = "Manual.pdf") -> DocumentEntry:
    return DocumentEntry(
        name=name,
        path=name,
        entry_type=DocumentEntryType.FILE,
        size_bytes=6,
        modified_at=datetime(2026, 7, 22, 10, 0, tzinfo=UTC),
        content_type="application/pdf",
    )


def test_documents_api_lists_and_downloads_without_remote_credentials(
    documents_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        DocumentService,
        "list_entries",
        lambda self, path="": DocumentListRead(
            path=path,
            root_path="docofhome/Documents",
            root_exists=True,
            items=[sample_entry()],
        ),
    )
    monkeypatch.setattr(
        DocumentService,
        "download",
        lambda self, path: DocumentDownload(
            filename="Handbuch Ä.pdf",
            content=b"manual",
            content_type="application/pdf",
            etag='"test-etag"',
        ),
    )

    listed = documents_client.get("/api/v1/documents", params={"path": ""})
    downloaded = documents_client.get(
        "/api/v1/documents/download",
        params={"path": "Manual.pdf"},
    )

    assert listed.status_code == 200
    assert listed.json()["items"][0]["name"] == "Manual.pdf"
    assert "nextcloud" not in listed.text.lower()
    assert downloaded.status_code == 200
    assert downloaded.content == b"manual"
    assert downloaded.headers["content-type"] == "application/pdf"
    assert "filename*=UTF-8''Handbuch%20%C3%84.pdf" in downloaded.headers["content-disposition"]
    assert downloaded.headers["x-content-type-options"] == "nosniff"
    assert downloaded.headers["cache-control"] == "private, no-store"


def test_documents_api_maps_conflicts_and_size_limits(
    documents_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def conflict(*args, **kwargs):
        raise DocumentConflictError("A document with this name already exists")

    monkeypatch.setattr(DocumentService, "create_folder", conflict)
    conflict_response = documents_client.post(
        "/api/v1/documents/folders",
        json={"parent_path": "", "name": "Invoices"},
    )
    assert conflict_response.status_code == 409

    def too_large(*args, **kwargs):
        raise DocumentTooLargeError("Document exceeds the 100 MB upload limit")

    monkeypatch.setattr(DocumentService, "upload", too_large)
    upload_response = documents_client.post(
        "/api/v1/documents/upload",
        params={"path": "", "filename": "large.bin"},
        content=b"small test body",
        headers={"Content-Type": "application/octet-stream"},
    )
    assert upload_response.status_code == 413


def test_documents_api_move_and_delete_contracts(
    documents_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    moved_payload: dict[str, str] = {}
    deleted: list[str] = []

    def move(self, source_path: str, target_parent_path: str, name: str):
        moved_payload.update(
            source_path=source_path,
            target_parent_path=target_parent_path,
            name=name,
        )
        return DocumentMutationRead(item=sample_entry(name))

    def delete(self, path: str) -> None:
        deleted.append(path)

    monkeypatch.setattr(DocumentService, "move", move)
    monkeypatch.setattr(DocumentService, "delete", delete)

    moved = documents_client.post(
        "/api/v1/documents/move",
        json={
            "source_path": "Manual.pdf",
            "target_parent_path": "Invoices",
            "name": "Manual 2026.pdf",
        },
    )
    removed = documents_client.delete(
        "/api/v1/documents",
        params={"path": "Invoices/Manual 2026.pdf"},
    )

    assert moved.status_code == 200
    assert moved_payload == {
        "source_path": "Manual.pdf",
        "target_parent_path": "Invoices",
        "name": "Manual 2026.pdf",
    }
    assert removed.status_code == 204
    assert deleted == ["Invoices/Manual 2026.pdf"]
