from dataclasses import dataclass
from uuid import UUID

from sqlmodel import Session, col, select

from app.electrical_phase_rail import rail_fully_covers_device, spans_overlap
from app.models.asset_engine import Asset
from app.models.electrical import (
    ElectricalAssetPlacement,
    ElectricalCabinetComponent,
    ElectricalComponent,
    ElectricalDistribution,
    ElectricalDistributionArea,
    ElectricalDistributionSection,
    ElectricalProtectiveDevice,
)
from app.services.din_width import effective_asset_module_width


@dataclass(frozen=True)
class ElectricalPlacementIssue(Exception):
    message: str
    conflict: bool = True

    def __str__(self) -> str:
        return self.message


def resolve_device_area(
    session: Session,
    distribution: ElectricalDistribution,
    area_id: UUID | None,
    *,
    positioned: bool,
) -> ElectricalDistributionArea | None:
    if distribution.layout_mode == "junction_box":
        raise ElectricalPlacementIssue(
            "In einer Verteilerdose können keine Schutzgeräte platziert werden."
        )
    if distribution.layout_mode == "sections":
        if area_id is None:
            if positioned:
                raise ElectricalPlacementIssue(
                    "Für ein platziertes Schutzgerät muss ein Gerätebereich ausgewählt werden.",
                    conflict=False,
                )
            return None
        area = session.get(ElectricalDistributionArea, area_id)
        if area is None or area.deleted_at is not None:
            raise ElectricalPlacementIssue(
                "Der ausgewählte Gerätebereich ist nicht verfügbar.", conflict=False
            )
        section = session.get(ElectricalDistributionSection, area.section_id)
        if (
            section is None
            or section.deleted_at is not None
            or section.distribution_id != distribution.id
        ):
            raise ElectricalPlacementIssue(
                "Der ausgewählte Gerätebereich gehört nicht zu dieser Verteilung.",
                conflict=False,
            )
        if area.area_type != "device_rows":
            raise ElectricalPlacementIssue(
                "Schutzgeräte können nur in einem Geräte- und Reihenbereich platziert werden.",
                conflict=False,
            )
        return area
    if area_id is not None:
        raise ElectricalPlacementIssue(
            "Die einfache Reihenaufteilung verwendet keinen DIN-Bereich.",
            conflict=False,
        )
    return None



def covering_phase_rails(
    session: Session,
    distribution_id: UUID,
    *,
    area_id: UUID | None,
    row_number: int,
    start_position: int,
    module_width: int,
    device_id: UUID | None = None,
) -> list[ElectricalCabinetComponent]:
    statement = select(ElectricalCabinetComponent).where(
        ElectricalCabinetComponent.distribution_id == distribution_id,
        ElectricalCabinetComponent.component_type == "phase_rail",
        ElectricalCabinetComponent.row_number == row_number,
        col(ElectricalCabinetComponent.deleted_at).is_(None),
    )
    statement = (
        statement.where(col(ElectricalCabinetComponent.area_id).is_(None))
        if area_id is None
        else statement.where(ElectricalCabinetComponent.area_id == area_id)
    )
    rails = [
        rail
        for rail in session.exec(statement).all()
        if rail_fully_covers_device(
            rail_start=rail.start_position,
            rail_width=rail.module_width,
            device_start=start_position,
            device_width=module_width,
        )
    ]
    return sorted(
        rails,
        key=lambda rail: (
            rail.module_width,
            rail.start_position,
            rail.name.casefold(),
            str(rail.id),
        ),
    )

def validate_protective_device_placement(
    session: Session,
    distribution: ElectricalDistribution,
    *,
    area_id: UUID | None,
    row_number: int,
    start_position: int,
    module_width: int,
    exclude_device_id: UUID | None = None,
) -> ElectricalDistributionArea | None:
    area = resolve_device_area(
        session, distribution, area_id, positioned=True
    )
    rows = area.rows if area is not None else distribution.rows
    modules_per_row = area.modules_per_row if area is not None else distribution.modules_per_row
    if rows is not None and row_number > rows:
        raise ElectricalPlacementIssue(
            f"Reihe {row_number} überschreitet die Kapazität von {rows} Reihen."
        )
    device_end = start_position + module_width - 1
    if modules_per_row is not None and device_end > modules_per_row:
        raise ElectricalPlacementIssue(
            f"Das Schutzgerät endet bei TE {device_end}; verfügbar sind nur "
            f"{modules_per_row} TE."
        )

    context_area_id = area.id if area else None
    device_statement = (
        select(ElectricalProtectiveDevice)
        .join(ElectricalComponent, ElectricalComponent.id == ElectricalProtectiveDevice.id)
        .where(
            ElectricalProtectiveDevice.distribution_id == distribution.id,
            col(ElectricalComponent.deleted_at).is_(None),
        )
    )
    device_statement = (
        device_statement.where(col(ElectricalProtectiveDevice.area_id).is_(None))
        if context_area_id is None
        else device_statement.where(ElectricalProtectiveDevice.area_id == context_area_id)
    )
    for other in session.exec(device_statement).all():
        if (
            other.id == exclude_device_id
            or other.row_number != row_number
            or other.start_position is None
        ):
            continue
        other_component = session.get(ElectricalComponent, other.id)
        other_asset = (
            session.get(Asset, other_component.asset_id)
            if other_component is not None
            else None
        )
        inherited_width = (
            effective_asset_module_width(session, other_asset)
            if other_asset is not None and other_asset.deleted_at is None
            else None
        )
        other_width = inherited_width if inherited_width is not None else other.module_width
        if other_width is None:
            continue
        if spans_overlap(
            start_position, module_width, other.start_position, other_width
        ):
            raise ElectricalPlacementIssue(
                "Die Position überschneidet sich mit einem vorhandenen Schutzgerät."
            )

    asset_statement = select(ElectricalAssetPlacement).where(
        ElectricalAssetPlacement.distribution_id == distribution.id,
        col(ElectricalAssetPlacement.deleted_at).is_(None),
    )
    asset_statement = (
        asset_statement.where(col(ElectricalAssetPlacement.area_id).is_(None))
        if context_area_id is None
        else asset_statement.where(ElectricalAssetPlacement.area_id == context_area_id)
    )
    for placement in session.exec(asset_statement).all():
        if placement.row_number != row_number:
            continue
        if spans_overlap(
            start_position,
            module_width,
            placement.start_position,
            placement.module_width,
        ):
            raise ElectricalPlacementIssue(
                "Die Position überschneidet sich mit einem vorhandenen DIN-Hutschienengerät."
            )

    component_statement = select(ElectricalCabinetComponent).where(
        ElectricalCabinetComponent.distribution_id == distribution.id,
        col(ElectricalCabinetComponent.deleted_at).is_(None),
    )
    component_statement = (
        component_statement.where(col(ElectricalCabinetComponent.area_id).is_(None))
        if context_area_id is None
        else component_statement.where(ElectricalCabinetComponent.area_id == context_area_id)
    )
    covering_phase_rails: list[ElectricalCabinetComponent] = []
    for component in session.exec(component_statement).all():
        if component.row_number != row_number:
            continue
        overlap = spans_overlap(
            start_position,
            module_width,
            component.start_position,
            component.module_width,
        )
        if not overlap:
            continue
        if component.component_type == "phase_rail":
            if not rail_fully_covers_device(
                rail_start=component.start_position,
                rail_width=component.module_width,
                device_start=start_position,
                device_width=module_width,
            ):
                raise ElectricalPlacementIssue(
                    "Eine Phasen-/Kammschiene darf ein Schutzgerät nicht nur teilweise "
                    "überdecken. Passe Schienenbereich oder Geräteposition an."
                )
            covering_phase_rails.append(component)
            continue
        if component.component_type == "busbar":
            # A general busbar is a non-TE overlay and has no positional phase authority.
            continue
        raise ElectricalPlacementIssue(
            "Die Position überschneidet sich mit einer vorhandenen Schrankkomponente."
        )

    if len(covering_phase_rails) > 1:
        names = ", ".join(sorted(rail.name for rail in covering_phase_rails))
        raise ElectricalPlacementIssue(
            "Ein Schutzgerät darf nur von einer Phasen-/Kammschiene versorgt werden. "
            f"Überlappende Schienen: {names}."
        )
    return area
