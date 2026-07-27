from app.repositories.electrical_topology import ElectricalEndpointProjection
from app.schemas.electrical_topology import ElectricalEndpointKind, ElectricalPhase
from app.services.electrical_topology import ElectricalTopologyService as BaseElectricalTopologyService


class ElectricalTopologyService(BaseElectricalTopologyService):
    """Topology service with authoritative rail-derived protective-device phases.

    Older connections may still contain a manually selected line phase. Once a
    protective device is covered by a comb/phase busbar, its effective line phase
    is derived from rail start phase and TE position. That calculated phase must
    replace the stored L1/L2/L3 value in every read representation. N and PE remain
    unchanged.
    """

    @staticmethod
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

            # A configured source/target component may further restrict the line
            # phases. A normal three-phase busbar leaves the calculated device
            # phase untouched.
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
            effective, inherited_warnings = (
                BaseElectricalTopologyService._effective_connection_phases(
                    source,
                    target,
                    stored,
                )
            )
            warnings.extend(inherited_warnings)
            return effective, warnings

        if effective != stored:
            stored_names = ", ".join(item.value for item in stored) or "keine"
            effective_names = ", ".join(item.value for item in effective) or "keine"
            warnings.append(
                "Gespeicherte Verbindung enthält abweichende Phasen: "
                f"{stored_names}. Wirksam: {effective_names}."
            )
        return effective, warnings
