from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, Text, text
from sqlmodel import Field, SQLModel


class WikiPage(SQLModel, table=True):
    __tablename__ = "wiki_pages"
    __table_args__ = (
        CheckConstraint(
            "sort_order >= 0 AND sort_order <= 100000",
            name="ck_wiki_pages_sort_order",
        ),
        Index(
            "uq_wiki_pages_active_slug",
            "slug",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    parent_id: UUID | None = Field(default=None, foreign_key="wiki_pages.id", index=True)
    title: str = Field(index=True, max_length=200)
    slug: str = Field(index=True, max_length=220)
    content: str = Field(default="", sa_type=Text)
    sort_order: int = Field(default=0, ge=0, le=100000, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = Field(default=None, index=True)


class DomainNote(SQLModel, table=True):
    __tablename__ = "domain_notes"
    __table_args__ = (
        CheckConstraint(
            "target_type IN ('asset', 'location', 'distribution', 'protective_device', 'circuit')",
            name="ck_domain_notes_target_type",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    target_type: str = Field(index=True, max_length=30)
    target_id: UUID = Field(index=True)
    content: str = Field(sa_type=Text)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = Field(default=None, index=True)
