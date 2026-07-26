from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlmodel import Field, SQLModel


class HomeAssistantAssetLink(SQLModel, table=True):
    __tablename__ = "home_assistant_asset_links"
    __table_args__ = (
        CheckConstraint(
            "object_type IN ('device', 'entity')",
            name="ck_home_assistant_asset_links_object_type",
        ),
        CheckConstraint(
            "role IN ('primary_live', 'total_power', 'voltage', 'current', 'energy', "
            "'power_l1', 'power_l2', 'power_l3', 'voltage_l1', 'voltage_l2', "
            "'voltage_l3', 'additional')",
            name="ck_home_assistant_asset_links_role",
        ),
        UniqueConstraint(
            "object_type",
            "external_id",
            name="uq_home_assistant_asset_links_external_object",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    object_type: str = Field(index=True, max_length=20)
    external_id: str = Field(index=True, max_length=255)
    asset_id: UUID = Field(foreign_key="assets.id", index=True)
    role: str = Field(default="additional", index=True, max_length=30)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HomeAssistantSelectionSetting(SQLModel, table=True):
    __tablename__ = "home_assistant_selection_settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_home_assistant_selection_settings_singleton"),
        CheckConstraint(
            "mode IN ('all', 'selected')",
            name="ck_home_assistant_selection_settings_mode",
        ),
    )

    id: int = Field(default=1, primary_key=True)
    mode: str = Field(default="all", max_length=20)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HomeAssistantEntitySelection(SQLModel, table=True):
    __tablename__ = "home_assistant_entity_selections"
    __table_args__ = (
        CheckConstraint(
            "setting_id = 1",
            name="ck_home_assistant_entity_selections_singleton",
        ),
        CheckConstraint(
            "length(trim(entity_id)) BETWEEN 3 AND 255 AND instr(entity_id, '.') > 1",
            name="ck_home_assistant_entity_selections_entity_id",
        ),
        UniqueConstraint(
            "entity_id",
            name="uq_home_assistant_entity_selections_entity_id",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    setting_id: int = Field(default=1, foreign_key="home_assistant_selection_settings.id")
    entity_id: str = Field(index=True, max_length=255)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
