from urllib.parse import quote

import httpx
import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.models.integration_setting import IntegrationSetting
from app.schemas.documents import DocumentEntryType
from app.services.documents import (
    MAX_DOCUMENT_BYTES,
    DocumentConfigurationError,
    DocumentConflictError,
    DocumentNotFoundError,
    DocumentRemoteError,
    DocumentService,
    DocumentTooLargeError,
    DocumentValidationError,
)


def document_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    session.add(
        IntegrationSetting(
            kind="nextcloud",
            enabled=True,
            base_url="https://nextcloud.example.test",
            account="document-user",
            secret="test-only-app-password",
            document_root="docofhome/Documents",
        )
    )
    session.commit()
    return session


def dav_response(
    path: str,
    *,
    folder: bool,
    size: int = 0,
    content_type: str | None = None,
) -> str:
    resource_type = (
        "<d:resourcetype><d:collection/></d:resourcetype>" if folder else "<d:resourcetype/>"
    )
    media_type = f"<d:getcontenttype>{content_type}</d:getcontenttype>" if content_type else ""
    return f"""
  <d:response>
    <d:href>{path}</d:href>
    <d:propstat><d:prop>
      {resource_type}
      <d:getcontentlength>{size}</d:getcontentlength>
      <d:getlastmodified>Wed, 22 Jul 2026 08:30:00 GMT</d:getlastmodified>
      {media_type}
      <d:getetag>\"etag-{size}\"</d:getetag>
    </d:prop><d:status>HTTP/1.1 200 OK</d:status></d:propstat>
  </d:response>"""


def multistatus(*responses: str) -> bytes:
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<d:multistatus xmlns:d="DAV:">' + "".join(responses) + "</d:multistatus>"
    ).encode()


def remote_path(suffix: str = "") -> str:
    base = "/remote.php/dav/files/document-user/docofhome/Documents"
    return f"{base}/{suffix}" if suffix else f"{base}/"


def test_document_list_is_scoped_sorted_and_typed() -> None:
    payload = multistatus(
        dav_response(remote_path(), folder=True),
        dav_response(
            remote_path("Manual.pdf"),
            folder=False,
            size=1234,
            content_type="application/pdf",
        ),
        dav_response(remote_path("Invoices/"), folder=True),
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PROPFIND"
        assert request.url.path == remote_path().rstrip("/")
        assert request.headers["depth"] == "1"
        assert request.headers["authorization"].startswith("Basic ")
        return httpx.Response(207, content=payload)

    result = DocumentService(
        document_session(), transport=httpx.MockTransport(handler)
    ).list_entries()

    assert result.root_path == "docofhome/Documents"
    assert result.root_exists is True
    assert [item.name for item in result.items] == ["Invoices", "Manual.pdf"]
    assert result.items[0].entry_type == DocumentEntryType.FOLDER
    assert result.items[1].content_type == "application/pdf"
    assert result.items[1].size_bytes == 1234


def test_missing_root_is_an_empty_first_run_state() -> None:
    service = DocumentService(
        document_session(),
        transport=httpx.MockTransport(lambda _: httpx.Response(404)),
    )

    result = service.list_entries()

    assert result.root_exists is False
    assert result.items == []


def test_create_folder_creates_root_hierarchy_but_rejects_existing_name() -> None:
    requests: list[tuple[str, str]] = []
    root_payload = multistatus(dav_response(remote_path(), folder=True))

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append((request.method, request.url.path))
        if request.method == "PROPFIND":
            return httpx.Response(207, content=root_payload)
        if request.url.path.endswith("/Invoices"):
            return httpx.Response(201)
        return httpx.Response(405)

    service = DocumentService(document_session(), transport=httpx.MockTransport(handler))
    created = service.create_folder("", "Invoices")

    assert created.created is True
    assert created.item.path == "Invoices"
    assert requests == [
        ("MKCOL", "/remote.php/dav/files/document-user/docofhome"),
        ("MKCOL", "/remote.php/dav/files/document-user/docofhome/Documents"),
        ("PROPFIND", "/remote.php/dav/files/document-user/docofhome/Documents"),
        ("MKCOL", "/remote.php/dav/files/document-user/docofhome/Documents/Invoices"),
    ]

    def conflict_handler(request: httpx.Request) -> httpx.Response:
        if request.method == "PROPFIND":
            return httpx.Response(207, content=root_payload)
        return httpx.Response(405)

    conflict = DocumentService(
        document_session(),
        transport=httpx.MockTransport(conflict_handler),
    )
    with pytest.raises(DocumentConflictError):
        conflict.create_folder("", "Invoices")


def test_upload_requires_explicit_overwrite_and_keeps_content_local_to_api() -> None:
    uploaded: list[httpx.Request] = []

    root_payload = multistatus(dav_response(remote_path(), folder=True))

    def conflict_handler(request: httpx.Request) -> httpx.Response:
        if request.method == "MKCOL":
            return httpx.Response(405)
        if request.method == "PROPFIND":
            return httpx.Response(207, content=root_payload)
        uploaded.append(request)
        assert request.headers["if-none-match"] == "*"
        assert request.content == b"manual"
        return httpx.Response(412)

    service = DocumentService(document_session(), transport=httpx.MockTransport(conflict_handler))
    with pytest.raises(DocumentConflictError):
        service.upload(
            "",
            "Manual.pdf",
            b"manual",
            content_type="application/pdf",
            overwrite=False,
        )

    def overwrite_handler(request: httpx.Request) -> httpx.Response:
        if request.method == "MKCOL":
            return httpx.Response(405)
        if request.method == "PROPFIND":
            return httpx.Response(207, content=root_payload)
        assert "if-none-match" not in request.headers
        assert request.headers["content-type"] == "application/pdf"
        return httpx.Response(204)

    replaced = DocumentService(
        document_session(), transport=httpx.MockTransport(overwrite_handler)
    ).upload(
        "",
        "Manual.pdf",
        b"manual",
        content_type="application/pdf; charset=binary",
        overwrite=True,
    )
    assert replaced.overwritten is True
    assert replaced.item.content_type == "application/pdf"


def test_upload_limit_and_path_traversal_fail_before_network() -> None:
    called = False

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(500)

    service = DocumentService(document_session(), transport=httpx.MockTransport(handler))

    with pytest.raises(DocumentTooLargeError):
        service.upload(
            "",
            "large.bin",
            b"x" * (MAX_DOCUMENT_BYTES + 1),
            content_type="application/octet-stream",
            overwrite=False,
        )
    for path in (
        "../secret",
        "/absolute",
        "folder\\file",
        "folder/../file",
        "folder/",
        "folder//file",
    ):
        with pytest.raises(DocumentValidationError):
            service.list_entries(path)
    assert called is False


def test_missing_relative_parent_is_not_created_implicitly() -> None:
    requests: list[httpx.Request] = []
    root_payload = multistatus(dav_response(remote_path(), folder=True))

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "MKCOL":
            return httpx.Response(405)
        if request.url.path.endswith("/Missing/Child"):
            return httpx.Response(404)
        return httpx.Response(207, content=root_payload)

    service = DocumentService(document_session(), transport=httpx.MockTransport(handler))
    with pytest.raises(DocumentNotFoundError):
        service.create_folder("Missing/Child", "Invoices")

    created_paths = [request.url.path for request in requests if request.method == "MKCOL"]
    assert created_paths == [
        "/remote.php/dav/files/document-user/docofhome",
        "/remote.php/dav/files/document-user/docofhome/Documents",
    ]


def test_out_of_scope_href_and_unsafe_xml_are_rejected() -> None:
    foreign_payload = multistatus(
        dav_response(
            "https://evil.example.test/remote.php/dav/files/document-user/"
            "docofhome/Documents/Manual.pdf",
            folder=False,
        )
    )
    service = DocumentService(
        document_session(),
        transport=httpx.MockTransport(lambda _: httpx.Response(207, content=foreign_payload)),
    )
    with pytest.raises(DocumentRemoteError):
        service.list_entries()

    unsafe_xml = b'<!DOCTYPE x [<!ENTITY y "z">]><d:multistatus xmlns:d="DAV:" />'
    service = DocumentService(
        document_session(),
        transport=httpx.MockTransport(lambda _: httpx.Response(207, content=unsafe_xml)),
    )
    with pytest.raises(DocumentRemoteError):
        service.list_entries()


def test_download_rename_and_delete_file_use_bounded_webdav_methods() -> None:
    file_payload = multistatus(
        dav_response(
            remote_path("Manual.pdf"),
            folder=False,
            size=6,
            content_type="application/pdf",
        )
    )
    root_payload = multistatus(dav_response(remote_path(), folder=True))
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "PROPFIND" and request.url.path.endswith("/Manual.pdf"):
            return httpx.Response(207, content=file_payload)
        if request.method == "PROPFIND":
            return httpx.Response(207, content=root_payload)
        if request.method == "GET":
            return httpx.Response(
                200,
                content=b"manual",
                headers={"Content-Type": "application/pdf", "ETag": '"remote-etag"'},
            )
        if request.method == "MOVE":
            assert request.headers["overwrite"] == "F"
            assert request.headers["destination"].endswith(
                f"/{quote('Renamed Manual.pdf', safe='')}"
            )
            return httpx.Response(201)
        if request.method == "DELETE":
            assert request.headers["if-match"] == '"etag-6"'
            return httpx.Response(204)
        raise AssertionError(request.method)

    service = DocumentService(document_session(), transport=httpx.MockTransport(handler))
    downloaded = service.download("Manual.pdf")
    moved = service.move("Manual.pdf", "", "Renamed Manual.pdf")
    service.delete("Manual.pdf")

    assert downloaded.content == b"manual"
    assert downloaded.etag == '"remote-etag"'
    assert moved.item.path == "Renamed Manual.pdf"
    assert [request.method for request in requests].count("MOVE") == 1
    assert [request.method for request in requests].count("DELETE") == 1


def test_empty_folder_delete_is_etag_guarded() -> None:
    folder_payload = multistatus(dav_response(remote_path("Empty/"), folder=True))
    listing_payload = multistatus(dav_response(remote_path("Empty/"), folder=True))
    delete_requests: list[httpx.Request] = []
    depth_zero_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal depth_zero_calls
        if request.method == "PROPFIND" and request.headers["depth"] == "0":
            depth_zero_calls += 1
            return httpx.Response(207, content=folder_payload)
        if request.method == "PROPFIND":
            return httpx.Response(207, content=listing_payload)
        if request.method == "DELETE":
            delete_requests.append(request)
            assert request.headers["if-match"] == '"etag-0"'
            return httpx.Response(204)
        raise AssertionError(request.method)

    service = DocumentService(document_session(), transport=httpx.MockTransport(handler))
    service.delete("Empty")

    assert depth_zero_calls == 2
    assert len(delete_requests) == 1


def test_folder_delete_precondition_failure_becomes_conflict() -> None:
    folder_payload = multistatus(dav_response(remote_path("Empty/"), folder=True))
    listing_payload = multistatus(dav_response(remote_path("Empty/"), folder=True))

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "PROPFIND" and request.headers["depth"] == "0":
            return httpx.Response(207, content=folder_payload)
        if request.method == "PROPFIND":
            return httpx.Response(207, content=listing_payload)
        if request.method == "DELETE":
            return httpx.Response(412)
        raise AssertionError(request.method)

    service = DocumentService(document_session(), transport=httpx.MockTransport(handler))
    with pytest.raises(DocumentConflictError):
        service.delete("Empty")


def test_non_empty_folder_cannot_be_deleted_recursively() -> None:
    folder_payload = multistatus(dav_response(remote_path("Invoices/"), folder=True))
    listing_payload = multistatus(
        dav_response(remote_path("Invoices/"), folder=True),
        dav_response(remote_path("Invoices/2026.pdf"), folder=False, size=10),
    )
    delete_called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal delete_called
        if request.method == "PROPFIND" and request.headers["depth"] == "0":
            return httpx.Response(207, content=folder_payload)
        if request.method == "PROPFIND":
            return httpx.Response(207, content=listing_payload)
        if request.method == "DELETE":
            delete_called = True
        return httpx.Response(500)

    service = DocumentService(document_session(), transport=httpx.MockTransport(handler))
    with pytest.raises(DocumentConflictError):
        service.delete("Invoices")
    assert delete_called is False


def test_empty_folder_without_collection_etag_can_be_deleted() -> None:
    folder_xml = dav_response(remote_path("Empty/"), folder=True).replace(
        '<d:getetag>"etag-0"</d:getetag>', ""
    )
    folder_payload = multistatus(folder_xml)
    listing_payload = multistatus(folder_xml)
    delete_requests: list[httpx.Request] = []
    listing_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal listing_calls
        if request.method == "PROPFIND" and request.headers["depth"] == "0":
            return httpx.Response(207, content=folder_payload)
        if request.method == "PROPFIND":
            listing_calls += 1
            return httpx.Response(207, content=listing_payload)
        if request.method == "DELETE":
            delete_requests.append(request)
            assert "if-match" not in request.headers
            return httpx.Response(204)
        raise AssertionError(request.method)

    service = DocumentService(document_session(), transport=httpx.MockTransport(handler))
    service.delete("Empty")

    assert listing_calls == 2
    assert len(delete_requests) == 1


def test_document_search_walks_subfolders_and_returns_ranked_matches() -> None:
    root_payload = multistatus(
        dav_response(remote_path(), folder=True),
        dav_response(remote_path("Rechnungen/"), folder=True),
        dav_response(remote_path("Baumplan.pdf"), folder=False, content_type="application/pdf"),
    )
    invoices_payload = multistatus(
        dav_response(remote_path("Rechnungen/"), folder=True),
        dav_response(
            remote_path("Rechnungen/Baumarkt 2026.pdf"),
            folder=False,
            content_type="application/pdf",
        ),
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PROPFIND"
        if request.url.path.endswith("/Rechnungen"):
            return httpx.Response(207, content=invoices_payload)
        return httpx.Response(207, content=root_payload)

    service = DocumentService(document_session(), transport=httpx.MockTransport(handler))
    results = service.search_entries("Baum", limit=5)

    assert [entry.path for entry in results] == [
        "Baumplan.pdf",
        "Rechnungen/Baumarkt 2026.pdf",
    ]


def test_disabled_nextcloud_does_not_attempt_remote_access() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        with pytest.raises(DocumentConfigurationError):
            DocumentService(session).list_entries()
