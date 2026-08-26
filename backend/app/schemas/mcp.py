from enum import StrEnum

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, TypeAdapter, field_validator


class McpPermission(StrEnum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class McpSettingsWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    permission: McpPermission = McpPermission.READ
    public_url: str | None = Field(default=None, max_length=2048)

    @field_validator("public_url")
    @classmethod
    def validate_public_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        validated = TypeAdapter(AnyHttpUrl).validate_python(value.strip())
        if validated.username is not None or validated.password is not None:
            raise ValueError("Die MCP-Adresse darf keine Zugangsdaten enthalten")
        if validated.query is not None or validated.fragment is not None:
            raise ValueError("Die MCP-Adresse darf keine Query-Parameter oder Fragmente enthalten")
        normalized = str(validated).rstrip("/")
        path = (validated.path or "").rstrip("/")
        if path != "/mcp":
            raise ValueError("Die öffentliche MCP-Adresse muss auf /mcp enden")
        return normalized


class McpSettingsRead(McpSettingsWrite):
    token_configured: bool


class McpTokenCreated(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str
    settings: McpSettingsRead
