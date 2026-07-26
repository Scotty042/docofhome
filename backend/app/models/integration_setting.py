from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class IntegrationSetting(SQLModel, table=True):
    """Persistent configuration for one optional external integration."""

    __tablename__ = "integration_settings"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    kind: str = Field(index=True, unique=True, max_length=50)
    enabled: bool = False
    base_url: str | None = Field(default=None, max_length=2048)
    account: str | None = Field(default=None, max_length=255)
    secret: str | None = None
    selected_album_id: str | None = Field(default=None, max_length=36)
    document_root: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
