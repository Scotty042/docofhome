from app.electrical_device_classification import (
    is_end_protective_asset_type_name,
    is_rcd_asset_type_name,
    protective_asset_device_type,
)


def test_rcd_asset_type_names_are_recognized() -> None:
    for value in (
        "FI-Schutzschalter",
        "FI/LS-Schalter",
        "RCD",
        "RCBO 4-polig",
        "Fehlerstrom-Schutzschalter",
        "Fehlerstromschutzschalter",
        "FI",
        "FI 4P",
    ):
        assert is_rcd_asset_type_name(value), value


def test_non_rcd_din_asset_type_names_are_not_recognized() -> None:
    for value in (
        "Sicherungsautomat",
        "Stromstoßschalter",
        "Smartes Relais / DIN-Schaltaktor",
        None,
    ):
        assert not is_rcd_asset_type_name(value), value


def test_circuit_end_protection_asset_types_are_classified() -> None:
    expected = {
        "Sicherungsautomat": "mcb",
        "Leitungsschutzschalter B16": "mcb",
        "LS-Schalter": "mcb",
        "Sicherung": "fuse",
        "Schmelzsicherung D02": "fuse",
        "FI/LS-Schalter": "rcbo",
        "RCBO 1P+N": "rcbo",
    }
    for value, device_type in expected.items():
        assert protective_asset_device_type(value) == device_type
        assert is_end_protective_asset_type_name(value)


def test_group_rcd_and_non_protective_assets_are_not_circuit_end_devices() -> None:
    for value in (
        "FI-Schutzschalter",
        "RCD 4-polig",
        "Überspannungsschutz",
        "Stromstoßschalter",
        "Smartes Relais / DIN-Schaltaktor",
        None,
    ):
        assert protective_asset_device_type(value) is None
        assert not is_end_protective_asset_type_name(value)
