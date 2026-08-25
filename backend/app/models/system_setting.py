from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class SystemSetting(SQLModel, table=True):
    """Persistent setting managed through the web interface.

    Secret values are stored locally but must never be returned by normal API
    responses or written to application logs.
    """

    __tablename__ = "system_settings"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    key: str = Field(index=True, unique=True, max_length=200)
    value: str
    is_secret: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
