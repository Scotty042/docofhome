from __future__ import annotations

import json
import ssl
from dataclasses import dataclass
from threading import Event
from typing import Any

import httpx


class BambuError(ValueError):
    pass


@dataclass
class SpoolPages:
    spools: list[dict[str, Any]]
    complete: bool = False
    warning: str | None = None
    repeated: bool = False
    unpaginated: bool = False
    total: int | None = None


class BambuCloud:
    path = "/v1/design-user-service/my/filament/v2"

    def __init__(
        self,
        token: str = "",
        region: str = "global",
        *,
        transport: httpx.BaseTransport | None = None,
    ):
        self.token = token
        self.base = "https://api.bambulab.cn" if region == "cn" else "https://api.bambulab.com"
        self.transport = transport

    def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = {"User-Agent": "BambuStudio/02.06.01", "Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            with httpx.Client(
                timeout=20, follow_redirects=False, trust_env=False, transport=self.transport
            ) as client:
                with client.stream(method, self.base + path, headers=headers, **kwargs) as response:
                    if not response.is_success:
                        raise BambuError(
                            f"Bambu-Anfrage fehlgeschlagen (HTTP {response.status_code}); "
                            "Anmeldung prüfen"
                        )
                    data = bytearray()
                    for chunk in response.iter_bytes():
                        data.extend(chunk)
                        if len(data) > 8 * 1024 * 1024:
                            raise BambuError("Bambu-Antwort überschreitet die Größenbegrenzung")
            result = json.loads(data)
            if not isinstance(result, dict):
                raise BambuError("Bambu liefert ein unbekanntes Antwortformat")
            if result.get("error") or result.get("code") not in (None, 0, "0"):
                raise BambuError("Bambu meldet einen Fehler; Zugang und Dienststatus prüfen")
            return result
        except (httpx.HTTPError, json.JSONDecodeError):
            raise BambuError("Bambu-Verbindung oder Antwort fehlerhaft") from None

    def login(self, account: str, password: str = "", code: str = "") -> dict[str, Any]:
        data = (
            {"account": account, "code": code}
            if code
            else {"account": account, "password": password}
        )
        return self.request("POST", "/v1/user-service/user/login", json=data)

    def uid(self) -> str:
        data = self.request("GET", "/v1/design-user-service/my/preference")
        value = str(data.get("uid", ""))
        if not value.isdecimal():
            raise BambuError("Bambu-Benutzerkennung konnte nicht bestätigt werden")
        return value

    def spools(self) -> dict[str, Any]:
        snapshot = self._spool_pages(20)
        if snapshot.repeated:
            # Restart at zero so a larger page can fetch additional IDs even
            # when the cloud ignores nonzero offsets.
            try:
                retry = self._spool_pages(100)
            except BambuError:
                retry = None
            first_ids = {str(row["id"]) for row in snapshot.spools}
            retry_ids = {str(row["id"]) for row in retry.spools} if retry else set()
            if (
                retry
                and retry.complete
                and first_ids <= retry_ids
                and (snapshot.total is None or snapshot.total == len(retry_ids))
            ):
                snapshot = retry
            elif (
                retry
                and snapshot.unpaginated
                and retry.repeated
                and snapshot.total is None
                and retry.total is None
                and first_ids == retry_ids
            ):
                # Studio reads the stock list at offset=0, limit=20 as a snapshot.
                # Require an oversized first response and identical IDs on the
                # larger retry before accepting a response that ignores paging.
                snapshot = SpoolPages(retry.spools, complete=True)
            else:
                if retry:
                    by_id = {str(row["id"]): row for row in snapshot.spools + retry.spools}
                    snapshot.spools = list(by_id.values())
                snapshot.warning = (
                    f"Bambu-Cloud-Abgleich unvollständig: {len(snapshot.spools)} Rollen empfangen. "
                    "Die Cloud liefert beim Blättern dieselben Rollen."
                )
        return {
            "spools": snapshot.spools,
            "complete": snapshot.complete,
            "warning": snapshot.warning,
        }

    def _spool_pages(self, limit: int) -> SpoolPages:
        items: dict[str, dict[str, Any]] = {}
        offset = 0
        warning = None
        expected_total = None
        repeated = False
        unpaginated = False
        for _page in range(250):
            try:
                result = self.request("GET", self.path, params={"offset": offset, "limit": limit})
            except BambuError as exc:
                if not items:
                    raise
                warning = str(exc)
                break
            hits = result.get("hits")
            if not isinstance(hits, list) or any(
                not isinstance(row, dict) or row.get("id") is None for row in hits
            ):
                warning = "Unbekanntes Cloud-Datenformat; Vollständigkeit nicht bestätigt"
                break
            total = result.get("total")
            if isinstance(total, dict):
                total = total.get("value")
            if (
                isinstance(total, str)
                and total.isascii()
                and total.isdecimal()
                and len(total) <= 12
            ):
                total = int(total)
            if type(total) is int and total >= 0:
                if expected_total is not None and total != expected_total:
                    warning = "Cloud-Rollenanzahl änderte sich während des Abgleichs"
                    break
                expected_total = total
            new = 0
            for row in hits:
                key = str(row["id"])
                if key not in items:
                    items[key] = row
                    new += 1
            if expected_total is not None and len(items) > expected_total:
                warning = "Cloud-Rollenanzahl widerspricht den gelieferten Daten"
                break
            if len(items) == expected_total or (not hits and expected_total is None):
                return SpoolPages(list(items.values()), complete=True)
            if not hits:
                warning = f"Bambu lieferte nur {len(items)} von {expected_total} Cloud-Rollen"
                break
            if offset == 0:
                unpaginated = len(items) == len(hits) and len(hits) > limit
            if not new:
                repeated = True
                unpaginated = (
                    unpaginated
                    and len(hits) == len(items) == offset
                    and len({str(row["id"]) for row in hits}) == len(items)
                )
                break
            if offset:
                unpaginated = False
            offset += len(hits)
            if len(items) >= 5000:
                warning = "Bestandsgrenze erreicht; Vollständigkeit nicht bestätigt"
                break
        return SpoolPages(
            list(items.values()),
            warning=warning or "Seitenlimit erreicht",
            repeated=repeated,
            unpaginated=unpaginated,
            total=expected_total,
        )

    def delete_spool(self, cloud_id: str) -> None:
        self.request("DELETE", self.path + "/batch", json={"ids": [cloud_id]})


def mqtt_snapshot(
    token: str, uid: str, serials: list[str], region: str = "global", *, timeout: float = 12
) -> dict[str, dict[str, Any]]:
    """Short, CA-verified cloud MQTT session; only subscribes and requests status."""
    import paho.mqtt.client as mqtt
    from paho.mqtt.enums import CallbackAPIVersion

    snapshots: dict[str, dict[str, Any]] = {}
    complete = Event()
    failed = Event()
    client = mqtt.Client(CallbackAPIVersion.VERSION2)
    client.username_pw_set(f"u_{uid}", token)
    client.tls_set_context(ssl.create_default_context())

    def connected(c: Any, _userdata: Any, _flags: Any, reason: Any, _properties: Any) -> None:
        if reason.is_failure:
            failed.set()
            complete.set()
            return
        c.subscribe([(f"device/{serial}/report", 0) for serial in serials])

    def subscribed(c: Any, _userdata: Any, _mid: Any, _codes: Any, _properties: Any) -> None:
        for serial in serials:
            c.publish(
                f"device/{serial}/request",
                json.dumps(
                    {
                        "pushing": {
                            "sequence_id": "0",
                            "command": "pushall",
                            "version": 1,
                            "push_target": 1,
                        }
                    }
                ),
            )

    def message(_c: Any, _userdata: Any, msg: Any) -> None:
        if len(msg.payload) > 2 * 1024 * 1024:
            return
        try:
            serial = msg.topic.split("/")[1]
            body = json.loads(msg.payload).get("print", {})
            if serial in serials and isinstance(body, dict):
                ams = body.get("ams", {}).get("ams") if isinstance(body.get("ams"), dict) else None
                if isinstance(ams, list):
                    snapshots[serial] = body
                    if len(snapshots) == len(serials):
                        complete.set()
        except (ValueError, IndexError, AttributeError):
            return

    client.on_connect = connected
    client.on_subscribe = subscribed
    client.on_message = message
    try:
        client.connect(
            "cn.mqtt.bambulab.com" if region == "cn" else "us.mqtt.bambulab.com", 8883, keepalive=30
        )
        client.loop_start()
        complete.wait(timeout)
        if failed.is_set() or not snapshots:
            raise BambuError(
                "Keine AMS-Statusdaten empfangen; Drucker, Cloud-Zugang und Kennungen prüfen"
            )
        return snapshots
    except (OSError, ValueError) as exc:
        if isinstance(exc, BambuError):
            raise
        raise BambuError("MQTT-Verbindung fehlgeschlagen") from None
    finally:
        client.disconnect()
        client.loop_stop()
