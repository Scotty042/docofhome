"""Shared phase-/comb-rail calculations.

The helpers in this module deliberately avoid database access.  Every service,
repository and migration-facing test can therefore use the same rules instead
of reimplementing subtly different TE and pole calculations.
"""

from app.schemas.electrical_topology import ElectricalPhase

LINE_PHASES: tuple[ElectricalPhase, ...] = (
    ElectricalPhase.L1,
    ElectricalPhase.L2,
    ElectricalPhase.L3,
)


def phase_pattern(
    *,
    phase_l1: bool,
    phase_l2: bool,
    phase_l3: bool,
    start_phase: str | None,
) -> tuple[ElectricalPhase, ...]:
    enabled = tuple(
        phase
        for phase, selected in (
            (ElectricalPhase.L1, phase_l1),
            (ElectricalPhase.L2, phase_l2),
            (ElectricalPhase.L3, phase_l3),
        )
        if selected
    )
    if not enabled:
        return ()
    start = (
        ElectricalPhase(start_phase)
        if start_phase in {phase.value for phase in LINE_PHASES}
        and ElectricalPhase(start_phase) in enabled
        else enabled[0]
    )
    index = LINE_PHASES.index(start)
    rotated = LINE_PHASES[index:] + LINE_PHASES[:index]
    return tuple(phase for phase in rotated if phase in enabled)


def active_line_pole_count(device_type: str, poles: int | None) -> int:
    """Return the number of active line conductors represented by ``poles``.

    RCD, RCBO and common SPD pole counts usually include a neutral pole
    (2P = L+N, 4P = L1+L2+L3+N).  Treating all poles as line phases caused
    impossible L1/L2 assignments on 1P+N devices.
    """

    count = max(1, poles or 1)
    if device_type in {"rcd", "rcbo", "spd"} and count in {2, 4}:
        count -= 1
    return min(3, count)


def span_end(start_position: int, module_width: int) -> int:
    return start_position + module_width - 1


def spans_overlap(
    first_start: int,
    first_width: int,
    second_start: int,
    second_width: int,
) -> bool:
    return (
        first_start <= span_end(second_start, second_width)
        and span_end(first_start, first_width) >= second_start
    )


def rail_fully_covers_device(
    *,
    rail_start: int,
    rail_width: int,
    device_start: int | None,
    device_width: int | None,
) -> bool:
    if device_start is None or device_width is None:
        return False
    return (
        rail_start <= device_start
        and span_end(device_start, device_width) <= span_end(rail_start, rail_width)
    )


def phase_rail_device_phases(
    *,
    rail_start: int,
    rail_width: int,
    phase_l1: bool,
    phase_l2: bool,
    phase_l3: bool,
    start_phase: str | None,
    device_start: int | None,
    device_width: int | None,
    device_type: str,
    poles: int | None,
) -> tuple[ElectricalPhase, ...]:
    if not rail_fully_covers_device(
        rail_start=rail_start,
        rail_width=rail_width,
        device_start=device_start,
        device_width=device_width,
    ):
        return ()
    pattern = phase_pattern(
        phase_l1=phase_l1,
        phase_l2=phase_l2,
        phase_l3=phase_l3,
        start_phase=start_phase,
    )
    if not pattern or device_start is None:
        return ()
    offset = device_start - rail_start
    count = active_line_pole_count(device_type, poles)
    return tuple(
        dict.fromkeys(pattern[(offset + index) % len(pattern)] for index in range(count))
    )


def phase_rail_din_asset_phases(
    *,
    rail_start: int,
    rail_width: int,
    phase_l1: bool,
    phase_l2: bool,
    phase_l3: bool,
    start_phase: str | None,
    asset_start: int | None,
    asset_width: int | None,
) -> tuple[ElectricalPhase, ...]:
    """Return all line phases contacted by a generic DIN device.

    Generic DIN placements do not carry a protective-device pole model. Their
    physical rail contacts therefore follow every occupied TE in the rail
    pattern. Duplicate phase names are collapsed while preserving L1/L2/L3
    order of first contact.
    """
    if not rail_fully_covers_device(
        rail_start=rail_start,
        rail_width=rail_width,
        device_start=asset_start,
        device_width=asset_width,
    ):
        return ()
    pattern = phase_pattern(
        phase_l1=phase_l1,
        phase_l2=phase_l2,
        phase_l3=phase_l3,
        start_phase=start_phase,
    )
    if not pattern or asset_start is None or asset_width is None:
        return ()
    offset = asset_start - rail_start
    return tuple(
        dict.fromkeys(
            pattern[(offset + index) % len(pattern)]
            for index in range(asset_width)
        )
    )
