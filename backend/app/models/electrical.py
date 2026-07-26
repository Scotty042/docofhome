from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DDL, Index, event, text
from sqlmodel import Field, SQLModel


class ElectricalComponent(SQLModel, table=True):
    __tablename__ = "electrical_components"
    __table_args__ = (
        CheckConstraint(
            "role IN ('distribution', 'protective_device')",
            name="ck_electrical_components_role",
        ),
        Index(
            "uq_electrical_components_active_asset",
            "asset_id",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    asset_id: UUID = Field(foreign_key="assets.id", index=True)
    role: str = Field(index=True, max_length=30)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = Field(default=None, index=True)


class ElectricalDistribution(SQLModel, table=True):
    __tablename__ = "electrical_distributions"
    __table_args__ = (
        CheckConstraint(
            "(distribution_type = 'main' AND parent_distribution_id IS NULL) OR "
            "(distribution_type = 'sub' AND parent_distribution_id IS NOT NULL)",
            name="ck_electrical_distributions_type_parent",
        ),
        CheckConstraint(
            "layout_mode IN ('rows', 'sections')",
            name="ck_electrical_distributions_layout_mode",
        ),
        CheckConstraint(
            "layout_mode = 'rows' OR (rows IS NULL AND modules_per_row IS NULL)",
            name="ck_electrical_distributions_section_capacity",
        ),
        CheckConstraint(
            "rows IS NULL OR (rows >= 1 AND rows <= 100)",
            name="ck_electrical_distributions_rows",
        ),
        CheckConstraint(
            "modules_per_row IS NULL OR (modules_per_row >= 1 AND modules_per_row <= 1000)",
            name="ck_electrical_distributions_modules",
        ),
    )

    id: UUID = Field(foreign_key="electrical_components.id", primary_key=True)
    parent_distribution_id: UUID | None = Field(
        default=None,
        foreign_key="electrical_distributions.id",
        index=True,
    )
    distribution_type: str = Field(index=True, max_length=20)
    layout_mode: str = Field(default="rows", index=True, max_length=20)
    designation: str | None = Field(default=None, index=True, max_length=150)
    rows: int | None = Field(default=None, ge=1, le=100)
    modules_per_row: int | None = Field(default=None, ge=1, le=1000)
    description: str | None = None
    notes: str | None = None


class ElectricalDistributionSection(SQLModel, table=True):
    __tablename__ = "electrical_distribution_sections"
    __table_args__ = (
        CheckConstraint(
            "position >= 1 AND position <= 50",
            name="ck_electrical_distribution_sections_position",
        ),
        Index(
            "uq_electrical_distribution_sections_active_position",
            "distribution_id",
            "position",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    distribution_id: UUID = Field(
        foreign_key="electrical_distributions.id",
        index=True,
    )
    name: str = Field(max_length=150)
    position: int = Field(ge=1, le=50)
    description: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = Field(default=None, index=True)


class ElectricalDistributionArea(SQLModel, table=True):
    __tablename__ = "electrical_distribution_areas"
    __table_args__ = (
        CheckConstraint(
            "area_type IN ('device_rows', 'meter', 'connection', 'neutral_rail', "
            "'protective_earth_rail', 'technology', 'reserve', 'cover')",
            name="ck_electrical_distribution_areas_type",
        ),
        CheckConstraint(
            "position >= 1 AND position <= 100",
            name="ck_electrical_distribution_areas_position",
        ),
        CheckConstraint(
            "width IN ('full', 'half')",
            name="ck_electrical_distribution_areas_width",
        ),
        CheckConstraint(
            "(width = 'full' AND side IS NULL) OR "
            "(width = 'half' AND side IN ('left', 'right'))",
            name="ck_electrical_distribution_areas_side",
        ),
        CheckConstraint(
            "rows IS NULL OR (rows >= 1 AND rows <= 100)",
            name="ck_electrical_distribution_areas_rows",
        ),
        CheckConstraint(
            "modules_per_row IS NULL OR (modules_per_row >= 1 AND modules_per_row <= 1000)",
            name="ck_electrical_distribution_areas_modules",
        ),
        CheckConstraint(
            "area_type = 'device_rows' OR (rows IS NULL AND modules_per_row IS NULL)",
            name="ck_electrical_distribution_areas_capacity_type",
        ),
        Index(
            "uq_electrical_distribution_areas_active_full_level",
            "section_id",
            "position",
            unique=True,
            sqlite_where=text("deleted_at IS NULL AND width = 'full'"),
        ),
        Index(
            "uq_electrical_distribution_areas_active_half_side",
            "section_id",
            "position",
            "side",
            unique=True,
            sqlite_where=text("deleted_at IS NULL AND width = 'half'"),
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    section_id: UUID = Field(
        foreign_key="electrical_distribution_sections.id",
        index=True,
    )
    name: str = Field(max_length=150)
    area_type: str = Field(index=True, max_length=30)
    position: int = Field(ge=1, le=100)
    rows: int | None = Field(default=None, ge=1, le=100)
    modules_per_row: int | None = Field(default=None, ge=1, le=1000)
    width: str = Field(default="full", max_length=10)
    side: str | None = Field(default=None, max_length=10)
    description: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = Field(default=None, index=True)


class ElectricalMeterPlacement(SQLModel, table=True):
    __tablename__ = "electrical_meter_placements"
    __table_args__ = (
        CheckConstraint(
            "position >= 1 AND position <= 100",
            name="ck_electrical_meter_placements_position",
        ),
        CheckConstraint(
            "(meter_id IS NOT NULL AND asset_id IS NULL) OR "
            "(meter_id IS NULL AND asset_id IS NOT NULL)",
            name="ck_electrical_meter_placements_source",
        ),
        Index(
            "uq_electrical_meter_placements_active_meter",
            "meter_id",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
        Index(
            "uq_electrical_meter_placements_active_asset",
            "asset_id",
            unique=True,
            sqlite_where=text("deleted_at IS NULL AND asset_id IS NOT NULL"),
        ),
        Index(
            "uq_electrical_meter_placements_active_area_position",
            "area_id",
            "position",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    distribution_id: UUID = Field(foreign_key="electrical_distributions.id", index=True)
    area_id: UUID = Field(foreign_key="electrical_distribution_areas.id", index=True)
    meter_id: UUID | None = Field(
        default=None,
        foreign_key="consumption_meters.id",
        index=True,
    )
    asset_id: UUID | None = Field(default=None, foreign_key="assets.id", index=True)
    position: int = Field(default=1, ge=1, le=100)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = Field(default=None, index=True)


class ElectricalAssetPlacement(SQLModel, table=True):
    __tablename__ = "electrical_asset_placements"
    __table_args__ = (
        CheckConstraint(
            "row_number >= 1 AND row_number <= 100",
            name="ck_electrical_asset_placements_row",
        ),
        CheckConstraint(
            "start_position >= 1 AND start_position <= 1000",
            name="ck_electrical_asset_placements_start",
        ),
        CheckConstraint(
            "module_width >= 1 AND module_width <= 100",
            name="ck_electrical_asset_placements_width",
        ),
        Index(
            "uq_electrical_asset_placements_active_asset",
            "asset_id",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
        Index(
            "ix_electrical_asset_placements_area_row",
            "area_id",
            "row_number",
            "start_position",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    distribution_id: UUID = Field(foreign_key="electrical_distributions.id", index=True)
    area_id: UUID | None = Field(
        default=None, foreign_key="electrical_distribution_areas.id", index=True
    )
    asset_id: UUID = Field(foreign_key="assets.id", index=True)
    row_number: int = Field(index=True, ge=1, le=100)
    start_position: int = Field(index=True, ge=1, le=1000)
    module_width: int = Field(ge=1, le=100)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = Field(default=None, index=True)


class ElectricalCabinetComponent(SQLModel, table=True):
    """Passive, non-asset component installed inside an electrical cabinet."""

    __tablename__ = "electrical_cabinet_components"
    __table_args__ = (
        CheckConstraint(
            "component_type IN ('phase_distribution_block', 'busbar', 'phase_rail', "
            "'neutral_rail', 'protective_earth_rail', 'terminal_block', "
            "'connection_block', 'potential_distribution', 'other')",
            name="ck_electrical_cabinet_components_type",
        ),
        CheckConstraint(
            "row_number >= 1 AND row_number <= 100",
            name="ck_electrical_cabinet_components_row",
        ),
        CheckConstraint(
            "start_position >= 1 AND start_position <= 1000",
            name="ck_electrical_cabinet_components_start",
        ),
        CheckConstraint(
            "module_width >= 1 AND module_width <= 100",
            name="ck_electrical_cabinet_components_width",
        ),
        CheckConstraint(
            "rated_current_a IS NULL OR (rated_current_a > 0 AND rated_current_a <= 10000)",
            name="ck_electrical_cabinet_components_current",
        ),
        CheckConstraint(
            "max_cross_section_mm2 IS NULL OR "
            "(max_cross_section_mm2 > 0 AND max_cross_section_mm2 <= 1000)",
            name="ck_electrical_cabinet_components_cross_section",
        ),
        CheckConstraint(
            "outgoing_connections IS NULL OR "
            "(outgoing_connections >= 1 AND outgoing_connections <= 1000)",
            name="ck_electrical_cabinet_components_outputs",
        ),
        CheckConstraint(
            "start_phase IS NULL OR start_phase IN ('L1', 'L2', 'L3')",
            name="ck_electrical_cabinet_components_start_phase",
        ),
        Index(
            "ix_electrical_cabinet_components_area_row",
            "area_id",
            "row_number",
            "start_position",
        ),
        Index(
            "ix_electrical_cabinet_components_distribution_row",
            "distribution_id",
            "row_number",
            "start_position",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    distribution_id: UUID = Field(foreign_key="electrical_distributions.id", index=True)
    area_id: UUID | None = Field(
        default=None, foreign_key="electrical_distribution_areas.id", index=True
    )
    component_type: str = Field(index=True, max_length=40)
    name: str = Field(max_length=150)
    row_number: int = Field(index=True, ge=1, le=100)
    start_position: int = Field(index=True, ge=1, le=1000)
    module_width: int = Field(ge=1, le=100)
    phase_l1: bool = False
    phase_l2: bool = False
    phase_l3: bool = False
    neutral: bool = False
    protective_earth: bool = False
    rated_current_a: float | None = Field(default=None, gt=0, le=10000)
    max_cross_section_mm2: float | None = Field(default=None, gt=0, le=1000)
    outgoing_connections: int | None = Field(default=None, ge=1, le=1000)
    linked_rcd_device_id: UUID | None = Field(
        default=None,
        foreign_key="electrical_protective_devices.id",
        index=True,
    )
    start_phase: str | None = Field(default=None, max_length=2)
    description: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = Field(default=None, index=True)


class ElectricalProtectiveDevice(SQLModel, table=True):
    __tablename__ = "electrical_protective_devices"
    __table_args__ = (
        CheckConstraint(
            "device_type IN ('fuse', 'rcd', 'mcb', 'rcbo', 'spd')",
            name="ck_electrical_protective_devices_type",
        ),
        CheckConstraint(
            "(row_number IS NULL AND start_position IS NULL "
            "AND module_width IS NULL) OR "
            "(row_number IS NOT NULL AND start_position IS NOT NULL "
            "AND module_width IS NOT NULL)",
            name="ck_electrical_protective_devices_position_group",
        ),
        CheckConstraint(
            "row_number IS NULL OR (row_number >= 1 AND row_number <= 100)",
            name="ck_electrical_protective_devices_row",
        ),
        CheckConstraint(
            "start_position IS NULL OR (start_position >= 1 AND start_position <= 1000)",
            name="ck_electrical_protective_devices_start",
        ),
        CheckConstraint(
            "module_width IS NULL OR (module_width >= 1 AND module_width <= 100)",
            name="ck_electrical_protective_devices_width",
        ),
        CheckConstraint(
            "rated_current_a IS NULL OR (rated_current_a > 0 AND rated_current_a <= 10000)",
            name="ck_electrical_protective_devices_current",
        ),
        CheckConstraint(
            "residual_current_ma IS NULL OR "
            "(residual_current_ma > 0 AND residual_current_ma <= 100000)",
            name="ck_electrical_protective_devices_residual",
        ),
        CheckConstraint(
            "poles IS NULL OR (poles >= 1 AND poles <= 12)",
            name="ck_electrical_protective_devices_poles",
        ),
        CheckConstraint(
            "breaking_capacity_ka IS NULL OR "
            "(breaking_capacity_ka > 0 AND breaking_capacity_ka <= 1000)",
            name="ck_electrical_protective_devices_breaking_capacity",
        ),
    )

    id: UUID = Field(foreign_key="electrical_components.id", primary_key=True)
    distribution_id: UUID = Field(
        foreign_key="electrical_distributions.id",
        index=True,
    )
    area_id: UUID | None = Field(
        default=None,
        foreign_key="electrical_distribution_areas.id",
        index=True,
    )
    device_type: str = Field(index=True, max_length=20)
    row_number: int | None = Field(default=None, index=True, ge=1, le=100)
    start_position: int | None = Field(
        default=None,
        index=True,
        ge=1,
        le=1000,
    )
    module_width: int | None = Field(default=None, ge=1, le=100)
    rated_current_a: float | None = Field(default=None, gt=0, le=10000)
    residual_current_ma: float | None = Field(default=None, gt=0, le=100000)
    characteristic: str | None = Field(default=None, max_length=30)
    poles: int | None = Field(default=None, ge=1, le=12)
    breaking_capacity_ka: float | None = Field(default=None, gt=0, le=1000)
    rcd_type: str | None = Field(default=None, max_length=80)
    fuse_type: str | None = Field(default=None, max_length=80)
    spd_type: str | None = Field(default=None, max_length=80)
    assigned_rcd_id: UUID | None = Field(
        default=None,
        foreign_key="electrical_protective_devices.id",
        index=True,
    )
    neutral_rail_id: UUID | None = Field(
        default=None,
        foreign_key="electrical_cabinet_components.id",
        index=True,
    )
    description: str | None = None
    notes: str | None = None


# SQLModel's create_all() is used by isolated tests. Keep its SQLite schema behavior
# aligned with Alembic by installing the same cross-table invariants there as well.
for trigger in (
    DDL(  # type: ignore[no-untyped-call]
        "CREATE TRIGGER IF NOT EXISTS trg_distribution_area_level_insert "
        "BEFORE INSERT ON electrical_distribution_areas "
        "WHEN NEW.deleted_at IS NULL AND EXISTS ("
        "SELECT 1 FROM electrical_distribution_areas existing "
        "WHERE existing.section_id = NEW.section_id "
        "AND existing.position = NEW.position "
        "AND existing.deleted_at IS NULL "
        "AND (NEW.width = 'full' OR existing.width = 'full')) "
        "BEGIN SELECT RAISE(ABORT, 'distribution area level conflict'); END"
    ),
    DDL(  # type: ignore[no-untyped-call]
        "CREATE TRIGGER IF NOT EXISTS trg_distribution_area_level_update "
        "BEFORE UPDATE OF section_id, position, width, side, deleted_at "
        "ON electrical_distribution_areas "
        "WHEN NEW.deleted_at IS NULL AND EXISTS ("
        "SELECT 1 FROM electrical_distribution_areas existing "
        "WHERE existing.id <> NEW.id "
        "AND existing.section_id = NEW.section_id "
        "AND existing.position = NEW.position "
        "AND existing.deleted_at IS NULL "
        "AND (NEW.width = 'full' OR existing.width = 'full')) "
        "BEGIN SELECT RAISE(ABORT, 'distribution area level conflict'); END"
    ),
):
    event.listen(
        ElectricalDistributionArea.__table__,  # type: ignore[attr-defined]
        "after_create",
        trigger.execute_if(dialect="sqlite"),
    )

event.listen(
    ElectricalComponent.__table__,  # type: ignore[attr-defined]
    "after_create",
    DDL(  # type: ignore[no-untyped-call]
        "CREATE TRIGGER IF NOT EXISTS trg_electrical_component_asset_immutable "
        "BEFORE UPDATE OF asset_id ON electrical_components "
        "WHEN NEW.asset_id <> OLD.asset_id BEGIN "
        "SELECT RAISE(ABORT, 'electrical role asset is immutable'); END"
    ).execute_if(dialect="sqlite"),
)

# Attach cross-table triggers after the final electrical table is created so every
# referenced table already exists in SQLModel create_all() test databases.
for trigger in (
    DDL(  # type: ignore[no-untyped-call]
        "CREATE TRIGGER IF NOT EXISTS trg_electrical_distribution_role_insert "
        "BEFORE INSERT ON electrical_distributions "
        "WHEN NOT EXISTS (SELECT 1 FROM electrical_components "
        "WHERE id = NEW.id AND role = 'distribution') BEGIN "
        "SELECT RAISE(ABORT, 'electrical distribution role mismatch'); END"
    ),
    DDL(  # type: ignore[no-untyped-call]
        "CREATE TRIGGER IF NOT EXISTS trg_electrical_distribution_role_update "
        "BEFORE UPDATE OF id ON electrical_distributions "
        "WHEN NOT EXISTS (SELECT 1 FROM electrical_components "
        "WHERE id = NEW.id AND role = 'distribution') BEGIN "
        "SELECT RAISE(ABORT, 'electrical distribution role mismatch'); END"
    ),
    DDL(  # type: ignore[no-untyped-call]
        "CREATE TRIGGER IF NOT EXISTS trg_electrical_device_role_insert "
        "BEFORE INSERT ON electrical_protective_devices "
        "WHEN NOT EXISTS (SELECT 1 FROM electrical_components "
        "WHERE id = NEW.id AND role = 'protective_device') BEGIN "
        "SELECT RAISE(ABORT, 'electrical protective-device role mismatch'); END"
    ),
    DDL(  # type: ignore[no-untyped-call]
        "CREATE TRIGGER IF NOT EXISTS trg_electrical_device_role_update "
        "BEFORE UPDATE OF id ON electrical_protective_devices "
        "WHEN NOT EXISTS (SELECT 1 FROM electrical_components "
        "WHERE id = NEW.id AND role = 'protective_device') BEGIN "
        "SELECT RAISE(ABORT, 'electrical protective-device role mismatch'); END"
    ),
    DDL(  # type: ignore[no-untyped-call]
        "CREATE TRIGGER IF NOT EXISTS trg_electrical_distribution_capacity_guard "
        "BEFORE UPDATE OF rows, modules_per_row ON electrical_distributions "
        "WHEN EXISTS ("
        "SELECT 1 FROM electrical_protective_devices device "
        "JOIN electrical_components component ON component.id = device.id "
        "WHERE device.distribution_id = OLD.id "
        "AND component.deleted_at IS NULL "
        "AND device.area_id IS NULL "
        "AND device.row_number IS NOT NULL "
        "AND ((NEW.rows IS NOT NULL AND device.row_number > NEW.rows) "
        "OR (NEW.modules_per_row IS NOT NULL "
        "AND device.start_position + device.module_width - 1 > NEW.modules_per_row))"
        ") BEGIN SELECT RAISE(ABORT, "
        "'distribution capacity conflicts with active protective devices'); END"
    ),
):
    event.listen(
        ElectricalProtectiveDevice.__table__,  # type: ignore[attr-defined]
        "after_create",
        trigger.execute_if(dialect="sqlite"),
    )
