import pytest
from pydantic import ValidationError

from app.schemas.mcp import McpSettingsWrite


def test_mcp_public_url_is_normalized_to_exact_endpoint() -> None:
    payload = McpSettingsWrite(public_url="https://mcp.example.test/mcp/")

    assert payload.public_url == "https://mcp.example.test/mcp"


@pytest.mark.parametrize(
    "url",
    [
        "https://mcp.example.test",
        "https://mcp.example.test/not-mcp",
        "https://user:secret@mcp.example.test/mcp",
        "https://mcp.example.test/mcp?token=secret",
        "https://mcp.example.test/mcp#fragment",
    ],
)
def test_mcp_public_url_rejects_ambiguous_or_embedded_credentials(url: str) -> None:
    with pytest.raises(ValidationError):
        McpSettingsWrite(public_url=url)
