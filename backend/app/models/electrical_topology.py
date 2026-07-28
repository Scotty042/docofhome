from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, text
from sqlmodel import Field, SQLModel


class ElectricalConnection(SQLModel, table=True):
    __tablename__ = "electrical_connections"
    __table_args__ = (
        CheckConstraint(
            "source_kind IN ('grid_connection', 'asset', 'distribution', "
            "'protective_device', 'cabinet_component', 'circuit')",
            name="ck_electrical_connections_source_kind",
        ),
        CheckConstraint(
            "target_kind IN ('asset', 'distribution', 'protective_device', "
            "'cabinet_component', 'circuit')",
            name="ck_electrical_connections_target_kind",
        ),
        CheckConstraint(
            "connection_type IN ('unknown', 'cable', 'wire', 'busbar', 'internal')",
            name="ck_electrical_connections_type",
        ),
        CheckConstraint(
            "phase_source IN ('manual', 'wire', 'busbar')",
            name="ck_electrical_connections_phase_source",
        ),
        CheckConstraint(
            "source_kind <> target_kind OR source_id <> target_id",
            name="ck_electrical_connections_distinct_endpoints",
        ),
        Index(
            "uq_electrical_connections_active_pair",
            "source_kind",
            "source_id",
            "target_kind",
            "target_id",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    source_kind: str = Field(index=True, max_length=30)
    source_id: UUID = Field(index=True)
    target_kind: str = Field(index=True, max_length=30)
    target_id: UUID = Field(index=True)
    connection_type: str = Field(default="unknown", index=True, max_length=20)
    label: str | None = Field(default=None, max_length=150)
    phase_l1: bool = False
    phase_l2: bool = False
    phase_l3: bool = False
    neutral: bool = False
    protective_earth: bool = False
    phase_source: str = Field(default="manual", index=True, max_length=20)
    source_connection_id: UUID | None = Field(default=None, index=True)
    cable_type: str | None = Field(default=None, max_length=150)
    cores: int | None = Field(default=None, ge=1, le=100)
    cross_section_mm2: float | None = Field(default=None, gt=0, le=1000)
    length_m: float | None = Field(default=None, gt=0, le=100000)
    route: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = Field(default=None, index=True)
