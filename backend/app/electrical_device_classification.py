from __future__ import annotations

import re


def _normalized(value: str | None) -> str:
    if not value:
        return ""
    normalized = value.casefold().replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", " ", normalized).strip()


def is_rcd_asset_type_name(value: str | None) -> bool:
    """Return whether an Asset-Type describes an FI/RCD or FI/LS/RCBO DIN device.

    New electrical cabinet devices are regular Assets.  Their electrical role is
    currently expressed by the Asset-Type name, so the cabinet association logic
    must use the same stable classification in API validation and presentation.
    """

    text = _normalized(value)
    if not text:
        return False
    tokens = set(text.split())
    compact = text.replace(" ", "")
    if "rcd" in tokens or "rcbo" in tokens or "fehlerstrom" in compact:
        return True
    # The default master data use names such as "FI-Schutzschalter" and
    # "FI/LS-Schalter". A standalone FI token is sufficiently specific inside
    # electrical Asset-Types and also supports user-created names such as "FI 4P".
    if "fi" in tokens:
        return True
    return False


def protective_asset_device_type(value: str | None) -> str | None:
    """Classify a current DIN Asset as an eligible circuit end-protection device.

    The current cabinet model stores newly placed DIN devices as regular Assets.
    A standalone FI/RCD remains a group protection device and is deliberately not
    eligible for a single circuit. Combined FI/LS and RCBO devices are eligible.
    """

    text = _normalized(value)
    if not text:
        return None
    tokens = set(text.split())
    compact = text.replace(" ", "")

    if "rcbo" in tokens or ("fi" in tokens and ("ls" in tokens or "lss" in tokens)):
        return "rcbo"
    if "mcb" in tokens or "leitungsschutzschalter" in compact or "sicherungsautomat" in compact:
        return "mcb"
    if "ls" in tokens or "lss" in tokens:
        return "mcb"
    if "fuse" in tokens or "sicherung" in tokens or "schmelzsicherung" in compact:
        return "fuse"
    return None


def is_end_protective_asset_type_name(value: str | None) -> bool:
    return protective_asset_device_type(value) is not None
