from uuid import uuid4

from app.repositories.electrical_topology import ElectricalEndpointProjection
from app.schemas.electrical_topology import ElectricalEndpointKind, ElectricalPhase
from app.services.electrical_topology_effective import ElectricalTopologyService


def endpoint(
    kind: ElectricalEndpointKind,
    phases: tuple[ElectricalPhase, ...] | None,
) -> ElectricalEndpointProjection:
    return ElectricalEndpointProjection(
        kind=kind,
        id=uuid4(),
        name="Test",
        code=None,
        type_name="Test",
        location_name=None,
        device_type=None,
        deleted_at=None,
        effective_phases=phases,
    )


def test_trockner_uses_l3_from_busbar_position_instead_of_stored_l1() -> None:
    source = endpoint(
        ElectricalEndpointKind.CABINET_COMPONENT,
        (ElectricalPhase.L1, ElectricalPhase.L2, ElectricalPhase.L3),
    )
    target = endpoint(
        ElectricalEndpointKind.PROTECTIVE_DEVICE,
        (ElectricalPhase.L3,),
    )

    effective, warnings = ElectricalTopologyService._effective_connection_phases(
        source,
        target,
        [ElectricalPhase.L1, ElectricalPhase.N, ElectricalPhase.PE],
    )

    assert effective == [ElectricalPhase.L3, ElectricalPhase.N, ElectricalPhase.PE]
    assert warnings == [
        "Gespeicherte Verbindung enthält abweichende Phasen: "
        "L1, N, PE. Wirksam: L3, N, PE."
    ]


def test_waschmaschine_uses_l2_instead_of_stored_l3() -> None:
    source = endpoint(
        ElectricalEndpointKind.CABINET_COMPONENT,
        (ElectricalPhase.L1, ElectricalPhase.L2, ElectricalPhase.L3),
    )
    target = endpoint(
        ElectricalEndpointKind.PROTECTIVE_DEVICE,
        (ElectricalPhase.L2,),
    )

    effective, warnings = ElectricalTopologyService._effective_connection_phases(
        source,
        target,
        [ElectricalPhase.L3],
    )

    assert effective == [ElectricalPhase.L2]
    assert warnings


def test_connection_without_rail_requirement_keeps_base_behavior() -> None:
    source = endpoint(
        ElectricalEndpointKind.ASSET,
        None,
    )
    target = endpoint(
        ElectricalEndpointKind.ASSET,
        None,
    )

    effective, warnings = ElectricalTopologyService._effective_connection_phases(
        source,
        target,
        [ElectricalPhase.L1, ElectricalPhase.N],
    )

    assert effective == [ElectricalPhase.L1, ElectricalPhase.N]
    assert warnings == []
