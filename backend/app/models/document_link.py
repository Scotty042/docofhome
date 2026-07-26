from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, text
from sqlmodel import Field, SQLModel


class DocumentLink(SQLModel, table=True):
    __tablename__ = "document_links"
    __table_args__ = (
        CheckConstraint(
            "target_type IN ('asset', 'location', 'distribution', 'protective_device', 'circuit')",
            name="ck_document_links_target_type",
        ),
        Index(
            "uq_document_links_active_target_path",
            "target_type",
            "target_id",
            "document_path",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    target_type: str = Field(index=True, max_length=30)
    target_id: UUID = Field(index=True)
    document_path: str = Field(max_length=1000)
    document_name: str = Field(max_length=255)
    document_etag: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = Field(default=None, index=True)
