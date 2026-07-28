from __future__ import annotations

import ipaddress
import socket
from datetime import UTC, datetime
from urllib.parse import urlsplit, urlunsplit
from xml.etree import ElementTree

import httpx

from app.schemas.release import FritzBoxDeviceRead


class FritzBoxConnectorError(RuntimeError):
    pass


class FritzBoxConnector:
    """Bounded, read-only TR-064 host discovery connector."""

    service_type = "urn:dslforum-org:service:Hosts:1"
    control_path = "/upnp/control/hosts"

    def __init__(
        self,
        *,
        base_url: str,
        account: str,
        secret: str,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = self._safe_base_url(base_url)
        self.account = account
        self.secret = secret
        self.transport = transport

    def devices(self) -> list[FritzBoxDeviceRead]:
        count_xml = self._soap("GetHostNumberOfEntries", "")
        count = min(self._integer(count_xml, "NewHostNumberOfEntries") or 0, 256)
        result: list[FritzBoxDeviceRead] = []
        for index in range(count):
            body = f"<NewIndex>{index}</NewIndex>"
            try:
                xml = self._soap("GetGenericHostEntry", body)
            except FritzBoxConnectorError:
                continue
            result.append(
                FritzBoxDeviceRead(
                    name=self._value(xml, "NewHostName") or "Unbekanntes Gerät",
                    mac_address=self._value(xml, "NewMACAddress"),
                    ipv4=self._value(xml, "NewIPAddress"),
                    ipv6=self._value(xml, "NewIPv6Address"),
                    active=self._value(xml, "NewActive") in {"1", "true", "True"},
                    interface_type=self._value(xml, "NewInterfaceType"),
                    connection_rate_mbps=self._integer(xml, "NewX_AVM-DE_Speed"),
                    connected_via=self._value(xml, "NewX_AVM-DE_Layer1Interface"),
                    last_seen=self._last_seen(xml),
                    dhcp_reservation=self._optional_bool(
                        self._value(xml, "NewX_AVM-DE_FixedAddress")
                    ),
                )
            )
        def sort_key(item: FritzBoxDeviceRead) -> tuple[int, int, str]:
            try:
                address = ipaddress.ip_address(item.ipv4 or "")
                if address.version == 4:
                    return (0, int(address), item.name.casefold())
            except ValueError:
                pass
            return (1, 0, item.name.casefold())

        return sorted(result, key=sort_key)

    def _soap(self, action: str, body: str) -> str:
        envelope = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
            's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
            f'<s:Body><u:{action} xmlns:u="{self.service_type}">{body}</u:{action}>'
            "</s:Body></s:Envelope>"
        )
        try:
            with httpx.Client(
                auth=httpx.DigestAuth(self.account, self.secret),
                timeout=httpx.Timeout(8.0, connect=3.0),
                follow_redirects=False,
                transport=self.transport,
            ) as client:
                response = client.post(
                    f"{self.base_url}{self.control_path}",
                    content=envelope.encode("utf-8"),
                    headers={
                        "Content-Type": 'text/xml; charset="utf-8"',
                        "SOAPAction": f'"{self.service_type}#{action}"',
                    },
                )
        except httpx.HTTPError as exc:
            raise FritzBoxConnectorError("FRITZ!Box ist nicht erreichbar") from exc
        if response.is_redirect:
            raise FritzBoxConnectorError("Unsichere Weiterleitung der FRITZ!Box abgelehnt")
        if response.status_code in {401, 403}:
            raise FritzBoxConnectorError("FRITZ!Box-Benutzer oder Kennwort wurden abgelehnt")
        if response.status_code == 404:
            raise FritzBoxConnectorError(
                "TR-064 wurde an der FRITZ!Box nicht gefunden. Aktiviere unter Heimnetz > Netzwerk > Netzwerkeinstellungen den Zugriff für Anwendungen und verwende die FRITZ!Box-Adresse ohne zusätzlichen Pfad."
            )
        if response.status_code != 200:
            raise FritzBoxConnectorError(f"FRITZ!Box antwortet mit HTTP {response.status_code}")
        if len(response.content) > 2 * 1024 * 1024:
            raise FritzBoxConnectorError("FRITZ!Box-Antwort überschreitet 2 MiB")
        text = response.text
        if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
            raise FritzBoxConnectorError("Unsicheres XML wurde abgelehnt")
        try:
            ElementTree.fromstring(text)
        except ElementTree.ParseError as exc:
            raise FritzBoxConnectorError("FRITZ!Box lieferte ungültiges XML") from exc
        return text

    @classmethod
    def _safe_base_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise FritzBoxConnectorError("FRITZ!Box-URL muss HTTP(S) verwenden")
        if parsed.username or parsed.password or parsed.path not in {"", "/"}:
            raise FritzBoxConnectorError(
                "FRITZ!Box-URL darf keine Zugangsdaten oder Pfade enthalten"
            )
        hostname = parsed.hostname.casefold()
        normalized_port = parsed.port
        if normalized_port is None:
            normalized_port = 49000 if parsed.scheme == "http" else 49443
        host = parsed.hostname or ""
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        normalized = urlunsplit((parsed.scheme, f"{host}:{normalized_port}", "", "", ""))
        if hostname == "fritz.box" or hostname.endswith(".local"):
            return normalized.rstrip("/")
        try:
            addresses = {str(item[4][0]) for item in socket.getaddrinfo(hostname, parsed.port)}
        except socket.gaierror as exc:
            raise FritzBoxConnectorError("FRITZ!Box-Hostname kann nicht aufgelöst werden") from exc
        if not addresses or any(not cls._local_address(address) for address in addresses):
            raise FritzBoxConnectorError("Nur lokale FRITZ!Box-Adressen sind erlaubt")
        return normalized.rstrip("/")

    @staticmethod
    def _local_address(value: str) -> bool:
        address = ipaddress.ip_address(value.split("%", 1)[0])
        return address.is_private or address.is_loopback or address.is_link_local

    @staticmethod
    def _value(xml: str, name: str) -> str | None:
        root = ElementTree.fromstring(xml)
        for element in root.iter():
            if element.tag.rsplit("}", 1)[-1] == name:
                value = (element.text or "").strip()
                return value or None
        return None

    @classmethod
    def _integer(cls, xml: str, name: str) -> int | None:
        value = cls._value(xml, name)
        try:
            return int(value) if value is not None else None
        except ValueError:
            return None

    @classmethod
    def _last_seen(cls, xml: str) -> datetime | None:
        seconds = cls._integer(xml, "NewLeaseTimeRemaining")
        if seconds is None:
            return None
        return datetime.now(UTC)

    @staticmethod
    def _optional_bool(value: str | None) -> bool | None:
        if value is None:
            return None
        return value in {"1", "true", "True"}
