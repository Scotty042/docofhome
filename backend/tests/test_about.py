from datetime import UTC, datetime
from io import BytesIO
from zipfile import ZipFile

import pytest
from pydantic import ValidationError
from sqlmodel import Session

from app.models.application_setting import ApplicationSetting
from app.schemas.about import FeedbackTechnicalInfo, FeedbackWrite
from app.services.about import AboutService


class FakePublicShareUploader:
    uploads: list[tuple[str, bytes, str]] = []

    def __init__(self, **_: object) -> None:
        pass

    def upload(self, filename: str, *, content: bytes, content_type: str) -> int:
        self.uploads.append((filename, content, content_type))
        return 201


def application(**overrides: object) -> ApplicationSetting:
    values: dict[str, object] = {
        "installation_name": "Testhaus",
        "language": "de",
        "timezone": "Europe/Berlin",
        "theme": "dark",
        "setup_completed_at": datetime.now(UTC),
    }
    values.update(overrides)
    return ApplicationSetting(**values)


def test_about_page_uses_central_version_and_source_controlled_sections(
    session: Session,
) -> None:
    session.add(application())
    session.commit()

    result = AboutService(session).read()

    assert result.version
    assert result.license_notice
    assert result.feedback_available is True
    assert result.releases
    assert any(item.current for item in result.releases)


def test_feedback_rejects_whitespace_only_required_fields() -> None:
    with pytest.raises(ValidationError):
        FeedbackWrite(
            category="other",
            subject="   ",
            description="          ",
        )


def test_feedback_requires_visible_consent_for_technical_information() -> None:
    with pytest.raises(ValidationError):
        FeedbackWrite(
            category="error",
            subject="Fehler im Dialog",
            description="Der Dialog kann nicht gespeichert werden.",
            include_technical_info=False,
            technical_info=FeedbackTechnicalInfo(app_version="1.4.2"),
        )


def test_feedback_is_uploaded_as_bounded_zip(
    session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    FakePublicShareUploader.uploads.clear()
    session.add(application())
    session.commit()
    monkeypatch.setattr(
        "app.services.about.NextcloudPublicShareUploader",
        FakePublicShareUploader,
    )

    result = AboutService(session).submit_feedback(
        FeedbackWrite(
            category="improvement",
            subject="Dashboard verbessern",
            description="Der direkte Aufruf der Ablesung ist sehr hilfreich.",
            current_page="/",
            include_technical_info=True,
            technical_info=FeedbackTechnicalInfo(
                app_version="1.4.2",
                route="/",
                user_agent="Test Browser",
                viewport="390 × 844",
            ),
        ),
        client_key="test-feedback-upload",
    )

    assert result.accepted is True
    filename, content, content_type = FakePublicShareUploader.uploads[0]
    assert filename.startswith("docofhome-feedback-") and filename.endswith(".zip")
    assert content_type == "application/zip"
    assert len(content) < 256 * 1024
    with ZipFile(BytesIO(content)) as archive:
        assert set(archive.namelist()) == {"feedback.md", "metadata.json", "README.txt"}
        markdown = archive.read("feedback.md")
        metadata = archive.read("metadata.json")
        assert b"Dashboard verbessern" in markdown
        assert b"Test Browser" in markdown
        assert b"secret" not in metadata.lower()
