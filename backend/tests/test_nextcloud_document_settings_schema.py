import pytest
from pydantic import ValidationError

from app.schemas.settings import IntegrationWrite


def test_nextcloud_document_root_is_normalized() -> None:
    configuration = IntegrationWrite(
        kind="nextcloud",
        enabled=True,
        base_url="https://nextcloud.example.test",
        account=" document-user ",
        secret=" test-only-secret ",
        document_root=" Haus / Dokumente ",
    )

    assert configuration.account == "document-user"
    assert configuration.document_root == "Haus/Dokumente"


@pytest.mark.parametrize(
    "document_root",
    ["../secret", "Haus//Dokumente", "Haus\\Dokumente", "Haus/./Dokumente"],
)
def test_nextcloud_document_root_rejects_unsafe_segments(document_root: str) -> None:
    with pytest.raises(ValidationError):
        IntegrationWrite(kind="nextcloud", document_root=document_root)


def test_document_root_is_rejected_for_other_integrations() -> None:
    with pytest.raises(ValidationError):
        IntegrationWrite(kind="immich", document_root="Haus/Dokumente")
