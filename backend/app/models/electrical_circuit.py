from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, Index, String, text
from sqlmodel import Field, SQLModel


class ElectricalCircuit(SQLModel, table=True):
    __tablename__ = "electrical_circuits"
    __table_args__ = (
        Index(
            "uq_electrical_circuits_active_number",
            "distribution_id",
            "circuit_number",
            unique=True,
            sqlite_where=text("deleted_at IS NULL AND circuit_number IS NOT NULL"),
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    distribution_id: UUID = Field(
        foreign_key="electrical_distributions.id",
        index=True,
    )
    protective_device_id: UUID | None = Field(
        default=None,
        foreign_key="electrical_protective_devices.id",
        index=True,
    )
    name: str = Field(max_length=150, index=True)
    circuit_number: str | None = Field(
        default=None,
        sa_column=Column(String(50, collation="NOCASE"), nullable=True),
    )
    description: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = Field(default=None, index=True)


class ElectricalCircuitAssetLink(SQLModel, table=True):
    __tablename__ = "electrical_circuit_asset_links"
    __table_args__ = (
        Index(
            "uq_electrical_circuit_asset_links_active",
            "circuit_id",
            "asset_id",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    circuit_id: UUID = Field(
        foreign_key="electrical_circuits.id",
        index=True,
    )
    asset_id: UUID = Field(foreign_key="assets.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = Field(default=None, index=True)
