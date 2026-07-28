"""Verify that phase-rail runtime uses the cabinet's inherited DIN width."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
service = (ROOT / "backend/app/services/phase_rail_connections.py").read_text()
layout = (ROOT / "backend/app/distribution_layout.py").read_text()
test = (ROOT / "backend/tests/test_electrical_layout.py").read_text()

required_service = (
    "from app.services.din_width import effective_asset_module_width",
    "def _device_module_width(",
    "return effective_asset_module_width(self.session, asset)",
    "width = self._device_module_width(device)",
    "and self._device_module_width(device) is not None",
    '"Phase-rail synchronization: rail=%s distribution=%s explicit_protective=%d "',
)
missing = [item for item in required_service if item not in service]
if missing:
    raise AssertionError("Breiten-Fallback fehlt: " + ", ".join(missing))


for fragment in (
    "def _protective_device_module_width(",
    "device_width = self._protective_device_module_width(device)",
):
    if fragment not in layout:
        raise AssertionError(f"Platzierungsprüfung verwendet nicht die wirksame Breite: {fragment}")

for forbidden in (
    "and device.module_width is not None",
    "device_width=device.module_width",
):
    if forbidden in service:
        raise AssertionError(f"Historische lokale Breitenlogik noch aktiv: {forbidden}")

required_test = (
    "stored.module_width = None",
    '"Sicherungsautomat", "module_width": 1',
    'assert rail["automatic_connection_count"] == 4',
)
missing_test = [item for item in required_test if item not in test]
if missing_test:
    raise AssertionError("Regressionstest unvollständig: " + ", ".join(missing_test))

print("Kammschienen-Breitenfallback: geerbte DIN-Breite und Regressionstest geprüft.")
