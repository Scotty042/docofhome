"""Central classification rules for electrical protective devices."""

from __future__ import annotations

import re
import unicodedata

PROTECTIVE_DEVICE_TYPES = frozenset({"fuse", "rcd", "mcb", "rcbo", "spd"})

_PROTECTIVE_ASSET_TYPE_NAMES = frozenset(
    {
        "fehlerstromschutzschalter",
        "fi",
        "fi ls",
        "fi rcd",
        "fi ls schalter",
        "fi schutzschalter",
        "leitungsschutzschalter",
        "ls",
        "rcbo",
        "schmelzsicherung",
        "sicherung",
        "sicherungsautomat",
        "uberspannungsschutz",
        "uberspannungsschutzgerat",
    }
)


def normalized_asset_type_name(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.strip().casefold().replace("ß", "ss"))
    ascii_value = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return " ".join(re.findall(r"[a-z0-9]+", ascii_value))


def is_protective_asset_type(value: str) -> bool:
    normalized = normalized_asset_type_name(value)
    compact = normalized.replace(" ", "")
    return normalized in _PROTECTIVE_ASSET_TYPE_NAMES or compact in {
        name.replace(" ", "") for name in _PROTECTIVE_ASSET_TYPE_NAMES
    }
