from pathlib import Path
import re


BACKEND_REPLACEMENT = '''    @staticmethod
def _effective_connection_phases(
    source: ElectricalEndpointProjection,
    target: ElectricalEndpointProjection,
    stored: list[ElectricalPhase],
) -> tuple[list[ElectricalPhase], list[str]]:
    line_phases = {
        ElectricalPhase.L1,
        ElectricalPhase.L2,
        ElectricalPhase.L3,
    }
    order = {phase: index for index, phase in enumerate(ElectricalPhase)}
    warnings: list[str] = []

    requirements: list[tuple[ElectricalPhase, ...]] = []
    for endpoint in (source, target):
        if (
            endpoint.kind != ElectricalEndpointKind.PROTECTIVE_DEVICE
            or endpoint.effective_phases is None
        ):
            continue
        required = tuple(
            phase for phase in endpoint.effective_phases if phase in line_phases
        )
        if required:
            requirements.append(required)

    if requirements:
        required = requirements[0]
        if any(candidate != required for candidate in requirements[1:]):
            details = " / ".join(
                ", ".join(phase.value for phase in candidate)
                for candidate in requirements
            )
            warnings.append(
                "Beteiligte Schutzgeräte haben widersprüchliche wirksame Phasen: "
                f"{details}."
            )
            required_lines = set.intersection(
                *(set(candidate) for candidate in requirements)
            )
        else:
            required_lines = set(required)

        effective_set = (set(stored) - line_phases) | required_lines
        for endpoint in (source, target):
            if (
                endpoint.kind == ElectricalEndpointKind.PROTECTIVE_DEVICE
                or endpoint.effective_phases is None
            ):
                continue
            endpoint_lines = set(endpoint.effective_phases) & line_phases
            if endpoint_lines:
                effective_set -= line_phases - endpoint_lines
        effective = sorted(effective_set, key=order.__getitem__)
    else:
        allowed = set(stored)
        for endpoint in (source, target):
            if endpoint.effective_phases is None:
                continue
            line_allowed = set(endpoint.effective_phases) & line_phases
            if line_allowed:
                allowed -= line_phases - line_allowed
        effective = sorted(allowed, key=order.__getitem__)

    if effective != stored:
        stored_names = ", ".join(item.value for item in stored) or "keine"
        effective_names = ", ".join(item.value for item in effective) or "keine"
        warnings.append(
            "Gespeicherte Verbindung enthält abweichende Phasen: "
            f"{stored_names}. Wirksam: {effective_names}."
        )
    return effective, warnings
'''


def indent_method(source: str) -> str:
    return "\n".join(("    " + line) if line else "" for line in source.splitlines()) + "\n"


def patch_backend() -> None:
    path = Path("backend/app/services/electrical_topology.py")
    source = path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"    @staticmethod\n"
        r"    def _effective_connection_phases\(.*?\n"
        r"        return effective, warnings\n",
        re.DOTALL,
    )
    updated, count = pattern.subn(indent_method(BACKEND_REPLACEMENT), source, count=1)
    if count != 1:
        raise SystemExit(f"Expected one backend function, replaced {count}")
    path.write_text(updated, encoding="utf-8")


def patch_frontend() -> None:
    path = Path("frontend/src/pages/ElectricalTopologyPage.vue")
    source = path.read_text(encoding="utf-8")
    old = (
        "function displayPhases(connection: ElectricalConnection): ElectricalPhase[] {\n"
        "  return connection.effective_phases.length ? connection.effective_phases : connection.phases\n"
        "}"
    )
    new = (
        "function displayPhases(connection: ElectricalConnection): ElectricalPhase[] {\n"
        "  return connection.effective_phases\n"
        "}"
    )
    if old not in source:
        raise SystemExit("Frontend fallback function not found")
    path.write_text(source.replace(old, new, 1), encoding="utf-8")


def add_regression_test() -> None:
    Path("backend/tests/test_effective_connection_phases.py").write_text(
        '''from uuid import uuid4

from app.repositories.electrical_topology import ElectricalEndpointProjection
from app.schemas.electrical_topology import ElectricalEndpointKind, ElectricalPhase
from app.services.electrical_topology import ElectricalTopologyService


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


def test_old_l1_is_replaced_by_calculated_l3_and_n_pe_remain() -> None:
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


def test_old_l3_is_replaced_by_calculated_l2() -> None:
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
''',
        encoding="utf-8",
    )


if __name__ == "__main__":
    patch_backend()
    patch_frontend()
    add_regression_test()
