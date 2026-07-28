import httpx
import pytest

from app.connectors.fritzbox import FritzBoxConnector, FritzBoxConnectorError


def soap(values: dict[str, str]) -> bytes:
    fields = "".join(f"<{name}>{value}</{name}>" for name, value in values.items())
    return (
        '<?xml version="1.0"?><s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">'
        f"<s:Body>{fields}</s:Body></s:Envelope>"
    ).encode()


def test_fritzbox_reads_hosts_with_bounded_read_only_soap() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        action = request.headers["SOAPAction"]
        if "GetHostNumberOfEntries" in action:
            return httpx.Response(200, content=soap({"NewHostNumberOfEntries": "1"}))
        return httpx.Response(
            200,
            content=soap(
                {
                    "NewHostName": "Notebook",
                    "NewMACAddress": "AA:BB:CC:DD:EE:FF",
                    "NewIPAddress": "192.168.178.20",
                    "NewActive": "1",
                    "NewInterfaceType": "802.11",
                    "NewX_AVM-DE_Speed": "866",
                    "NewX_AVM-DE_Layer1Interface": "WLAN",
                    "NewX_AVM-DE_FixedAddress": "1",
                }
            ),
        )

    devices = FritzBoxConnector(
        base_url="http://fritz.box",
        account="readonly",
        secret="test-secret",
        transport=httpx.MockTransport(handler),
    ).devices()
    assert devices[0].mac_address == "AA:BB:CC:DD:EE:FF"
    assert devices[0].active is True
    assert all(request.method == "POST" for request in requests)
    assert all(request.url.path == "/upnp/control/hosts" for request in requests)


@pytest.mark.parametrize(
    "url",
    [
        "https://8.8.8.8",
        "http://user:secret@fritz.box",
        "http://fritz.box/admin",
        "file:///etc/passwd",
    ],
)
def test_fritzbox_rejects_nonlocal_or_unsafe_urls(url: str) -> None:
    with pytest.raises(FritzBoxConnectorError):
        FritzBoxConnector(base_url=url, account="readonly", secret="secret")


def test_fritzbox_rejects_redirects_and_unsafe_xml() -> None:
    redirect = httpx.MockTransport(lambda _request: httpx.Response(302, headers={"Location": "/"}))
    connector = FritzBoxConnector(
        base_url="http://fritz.box",
        account="readonly",
        secret="secret",
        transport=redirect,
    )
    with pytest.raises(FritzBoxConnectorError, match="Weiterleitung"):
        connector.devices()

    unsafe = httpx.MockTransport(
        lambda _request: httpx.Response(200, text="<!DOCTYPE x [<!ENTITY y SYSTEM 'file:///x'>]><x/>")
    )
    connector = FritzBoxConnector(
        base_url="http://fritz.box",
        account="readonly",
        secret="secret",
        transport=unsafe,
    )
    with pytest.raises(FritzBoxConnectorError, match="Unsicheres XML"):
        connector.devices()


def test_fritzbox_sorts_ipv4_numerically_and_invalid_addresses_last() -> None:
    hosts = [
        ("Hundred", "192.168.178.100"),
        ("Ten", "192.168.178.10"),
        ("One", "192.168.178.1"),
        ("Unknown", ""),
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        action = request.headers["SOAPAction"]
        if "GetHostNumberOfEntries" in action:
            return httpx.Response(200, content=soap({"NewHostNumberOfEntries": str(len(hosts))}))
        body = request.content.decode()
        index = int(body.split("<NewIndex>", 1)[1].split("</NewIndex>", 1)[0])
        name, address = hosts[index]
        return httpx.Response(
            200,
            content=soap({
                "NewHostName": name,
                "NewMACAddress": f"AA:BB:CC:DD:EE:{index:02X}",
                "NewIPAddress": address,
                "NewActive": "1",
            }),
        )

    devices = FritzBoxConnector(
        base_url="http://fritz.box",
        account="readonly",
        secret="secret",
        transport=httpx.MockTransport(handler),
    ).devices()
    assert [item.ipv4 for item in devices] == [
        "192.168.178.1",
        "192.168.178.10",
        "192.168.178.100",
        None,
    ]
