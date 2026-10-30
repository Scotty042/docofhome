import json
import sqlite3
from io import BytesIO
from uuid import UUID
from zipfile import ZipFile

import httpx
import pytest
import test_release_1718 as release_tests
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from PIL import Image
from pypdf import PdfReader
from sqlmodel import Session, SQLModel, create_engine

from app.connectors.bambu import BambuCloud, BambuError, mqtt_snapshot
from app.core.restore_pending import apply_pending_restore
from app.core.settings import settings
from app.main import app
from app.schemas.filament import FilamentConfig, LabelRequest, SpoolWrite
from app.schemas.mcp import McpSettingsWrite
from app.services.backups import BackupService
from app.services.filament import FilamentService
from app.services.filament_images import image_path, store_image
from app.services.filament_labels import labels
from app.services.mcp_settings import McpSettingsService
from app.services.release import PortabilityService


@pytest.fixture
def database(tmp_path, monkeypatch):
    yield from release_tests.database.__wrapped__(tmp_path, monkeypatch)


def cloud_row(id=1, **changes):
    return {
        "id": id,
        "filamentVendor": "Bambu Lab",
        "filamentType": "PLA",
        "filamentName": "PLA Basic",
        "color": "#008844",
        "netWeight": 390,
        "totalNetWeight": 1000,
        "RFID": "ABC123",
        "amsId": 0,
        "slotId": "0",
        "devId": "PRINTER",
        "inPrinter": True,
        **changes,
    }


def linked(service):
    service.store("account", "account-test")
    service.session.commit()
    service.import_cloud([cloud_row()], account="account-test", complete=True)
    return service.search()["items"][0]


def test_manual_manufacturers_filters_and_archival(session):
    service = FilamentService(session)
    row = service.save(
        SpoolWrite(
            manufacturer="SUNLU",
            material="ABS",
            condition="open",
            reorder=True,
            reorder_note="2 Rollen",
            remaining_g=0,
        )
    )
    assert row.label_code.startswith("FIL-") and row.remaining_g == 0
    assert service.search(material="PLA")["total"] == 0
    assert (
        service.search(material="ABS", manufacturer="SUNLU", condition="open", reorder=True)[
            "total"
        ]
        == 1
    )
    service.archive(row.id)
    assert service.search()["total"] == 0 and service.search(archive="archived")["total"] == 1
    service.archive(row.id, restore=True)
    assert service.search()["items"][0]["label_code"] == row.label_code


def test_sync_preserves_local_fields_archive_and_missing_cloud(session):
    service = FilamentService(session)
    original = linked(service)
    ident = UUID(original["id"])
    assert service.search("ABC123", archive="all")["total"] == 1
    service.save(
        SpoolWrite.model_validate(
            {
                **{k: original[k] for k in SpoolWrite.model_fields},
                "color_name": "Mistelzweig-Grün",
                "shop_code": "10502",
                "condition": "open",
                "reorder": True,
                "notes": "Persönliche Notiz",
            }
        ),
        ident,
    )
    service.archive(ident)
    service.import_cloud([cloud_row(netWeight=120)], account="account-test", complete=True)
    row = service.read(service.get(ident))
    assert row.archived_at and row.remaining_g == 120
    assert row.notes == "Persönliche Notiz" and row.shop_code == "10502" and row.reorder
    assert service.search(archive="all")["total"] == 1 and row.last_seen_at is None
    service.import_cloud([], account="account-test", complete=False)
    assert service.get(ident).cloud_present
    service.import_cloud([], account="account-test", complete=True)
    assert service.get(ident).cloud_present is False
    assert service.search(archive="all")["total"] == 1


def test_no_matching_by_color_or_zero_rfid_and_account_separation(session):
    service = FilamentService(session)
    service.import_cloud(
        [cloud_row(1, RFID="0000", netWeight=-1), cloud_row(2, RFID="0000")],
        account="one",
        complete=True,
    )
    assert service.search()["total"] == 2
    assert any(v["remaining_g"] is None for v in service.search()["items"])
    service.import_cloud([cloud_row(1)], account="two", complete=True)
    assert service.search()["total"] == 3


def test_short_pagination_and_repeated_pages():
    offsets = []

    def response(req):
        offset = int(req.url.params["offset"])
        offsets.append(offset)
        return httpx.Response(
            200, json={"hits": [cloud_row(offset + 1), cloud_row(offset + 2)] if offset < 4 else []}
        )

    result = BambuCloud("secret", transport=httpx.MockTransport(response)).spools()
    assert offsets == [0, 2, 4] and result["complete"] and len(result["spools"]) == 4
    repeated = BambuCloud(
        "secret",
        transport=httpx.MockTransport(
            lambda req: httpx.Response(200, json={"hits": [cloud_row()]})
        ),
    ).spools()
    assert not repeated["complete"] and len(repeated["spools"]) == 1 and repeated["warning"]


def test_cloud_login_codes_delete_and_error_redaction():
    requests = []
    client = BambuCloud(
        region="cn",
        transport=httpx.MockTransport(
            lambda req: requests.append(req) or httpx.Response(200, json={})
        ),
    )
    client.login("test@example.invalid", password="password", code="123456")
    assert json.loads(requests[0].content) == {"account": "test@example.invalid", "code": "123456"}
    client.delete_spool("42")
    assert requests[-1].method == "DELETE" and requests[-1].url.path.endswith("/filament/v2/batch")
    assert json.loads(requests[-1].content) == {"ids": ["42"]}
    assert requests[-1].url.host == "api.bambulab.cn"
    with pytest.raises(BambuError) as exc:
        BambuCloud(
            "TOKEN", transport=httpx.MockTransport(lambda req: httpx.Response(401, text="TOKEN"))
        ).spools()
    assert "TOKEN" not in str(exc.value)


def test_archive_cloud_deletion_explicit_and_local_survives_error(session, monkeypatch):
    service = FilamentService(session)
    source = linked(service)
    ident = UUID(source["id"])
    calls = []
    monkeypatch.setattr(
        service,
        "cloud",
        lambda: type("Cloud", (), {"delete_spool": lambda _, value: calls.append(value)})(),
    )
    service.archive(ident)
    assert not calls
    service.archive(ident, delete_cloud=True)
    assert calls == ["1"]

    def fail(_value):
        raise BambuError("HTTP 500")

    monkeypatch.setattr(
        service, "cloud", lambda: type("Cloud", (), {"delete_spool": lambda _, v: fail(v)})()
    )
    assert service.archive(ident, delete_cloud=True)["warning"]
    assert service.get(ident).archived_at is not None


def mqtt_data(tray):
    return {"PRINTER": {"ams": {"tray_exist_bits": "1", "ams": [{"id": "0", "tray": [tray]}]}}}


def test_mqtt_exact_matching_partial_updates_empty_slots_and_last_seen(session):
    service = FilamentService(session)
    source = linked(service)
    ident = UUID(source["id"])
    assert service.get(ident).last_seen_at is None
    service.apply_mqtt(
        mqtt_data(
            {"id": "0", "tray_type": "PLA", "tray_uuid": "ABC123", "tag_uid": "CHIP", "remain": 0}
        )
    )
    row = service.get(ident)
    assert row.last_seen_at is not None and row.slot_id == "0" and row.remaining_percent == 0
    service.apply_mqtt(mqtt_data({"id": "0", "remain": -1}))
    assert service.get(ident).slot_id == "0" and service.get(ident).remaining_percent is None
    service.import_cloud([cloud_row()], account="account-test", complete=True)
    assert service.get(ident).last_seen_at is not None
    service.apply_mqtt(mqtt_data({"id": "0"}))
    assert service.get(ident).slot_id is None and service.slots()[0]["occupied"] is False
    assert service.get(ident).last_seen_at is not None


def test_unknown_slots_need_manual_binding_and_archived_not_auto_linked(session):
    service = FilamentService(session)
    spool = service.save(SpoolWrite(material="PETG", manufacturer="SUNLU"))
    service.apply_mqtt(
        mqtt_data(
            {"id": "0", "tray_type": "PETG", "tray_uuid": "0000", "tag_uid": "0000", "remain": -1}
        )
    )
    slot = service.slots()[0]
    assert slot["spool_id"] is None and slot["remaining_percent"] is None
    service.bind_slot(UUID(slot["id"]), spool.id)
    assert service.get(spool.id).last_seen_at
    service.apply_mqtt(
        mqtt_data({"id": "0", "tray_type": "PETG", "tray_uuid": "0000", "tag_uid": "0000"})
    )
    assert service.slots()[0]["spool_id"] == str(spool.id)
    service.archive(spool.id)
    assert service.slots()[0]["spool_id"] is None
    with pytest.raises(ValueError):
        service.bind_slot(UUID(slot["id"]), spool.id)


def test_label_pdf_dimensions_jpeg_zip_and_actual_qr(session):
    import zxingcpp

    service = FilamentService(session)
    config = FilamentConfig(public_url="https://home.example.test")
    service.save_config(config)
    first = service.save(
        SpoolWrite(
            material="PLA",
            manufacturer="Bambu Lab",
            variant="PLA Basic",
            color_name="Mistelzweig-Grün",
            shop_code="10502",
        )
    )
    second = service.save(SpoolWrite(material="PETG", manufacturer="SUNLU", color_name="Schwarz"))
    content, media, _ = labels(session, LabelRequest(ids=[first.id, second.id]))
    doc = PdfReader(BytesIO(content))
    assert media == "application/pdf" and len(doc.pages) == 2
    assert abs(float(doc.pages[0].mediabox.width) - 40 * 72 / 25.4) < 0.01
    assert abs(float(doc.pages[0].mediabox.height) - 30 * 72 / 25.4) < 0.01
    jpg, media, _ = labels(session, LabelRequest(ids=[first.id], format="jpg"))
    image = Image.open(BytesIO(jpg))
    assert image.size == (472, 354) and image.info["dpi"] == (300, 300)
    decoded = zxingcpp.read_barcodes(image)
    assert decoded and decoded[0].text == f"https://home.example.test/filament/{first.id}"
    zipped, media, _ = labels(session, LabelRequest(ids=[first.id, second.id], format="jpg"))
    assert media == "application/zip"
    with ZipFile(BytesIO(zipped)) as archive:
        assert len(archive.namelist()) == 2


def test_store_image_exact_variant_cache_and_refuse_ambiguous(session, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    service = FilamentService(session)
    spool = service.save(
        SpoolWrite(material="PLA", variant="PLA Basic", manufacturer="Bambu Lab", shop_code="10502")
    )
    image = BytesIO()
    Image.new("RGB", (20, 20), "green").save(image, format="PNG")

    def response(req):
        return (
            httpx.Response(
                200,
                text='<script id="product-jsonld" type="application/ld+json">'
                + json.dumps(
                    {
                        "hasVariant": [
                            {
                                "name": "Mistletoe Green (10502)",
                                "image": "https://store.bblcdn.eu/test.png",
                            }
                        ]
                    }
                )
                + "</script>",
            )
            if req.url.host == "eu.store.bambulab.com"
            else httpx.Response(200, content=image.getvalue())
        )

    result = store_image(session, spool.id, transport=httpx.MockTransport(response))
    assert result.image_verified and result.image_url.startswith("/api/v1/filament/images/")
    assert image_path(result.image_url.rsplit("/", 1)[1]).is_file()
    with pytest.raises(ValueError):
        store_image(
            session,
            spool.id,
            transport=httpx.MockTransport(lambda req: httpx.Response(200, json={"variants": []})),
        )


def test_real_mcp_crud_filters_archive_and_permissions(database):
    session, token = database
    with TestClient(app) as client:
        saved = release_tests.call(
            client,
            token,
            "save_filament_spool",
            {
                "data": {
                    "manufacturer": "SUNLU",
                    "material": "ASA",
                    "reorder": True,
                    "remaining_g": 0,
                }
            },
        )["item"]
        changed = release_tests.call(
            client,
            token,
            "save_filament_spool",
            {"spool_id": saved["id"], "data": {"reorder_note": "2 Refills"}},
        )["item"]
        assert changed["remaining_g"] == 0 and changed["material"] == "ASA"
        FilamentService(session).save_config(FilamentConfig(public_url="https://home.example.test"))
        label = release_tests.call(
            client, token, "create_filament_labels", {"spool_ids": [saved["id"]]}
        )
        from urllib.parse import urlsplit

        downloaded = client.get(urlsplit(label["download_url"]).path)
        assert label["valid_hours"] == 24 and downloaded.status_code == 200
        assert len(PdfReader(BytesIO(downloaded.content)).pages) == 1
        assert (
            release_tests.call(
                client,
                token,
                "search_filament_spools",
                {"material": "ASA", "reorder": True},
                path=True,
            )["total"]
            == 1
        )
        release_tests.call(client, token, "archive_filament_spool", {"spool_id": saved["id"]})
        assert release_tests.call(client, token, "search_filament_spools", {})["total"] == 0
        assert release_tests.call(client, token, "get_filament_spool", {"spool_id": saved["id"]})[
            "archived_at"
        ]
        McpSettingsService(session).update(McpSettingsWrite(enabled=True, permission="read"))
        denied = client.post(
            f"/mcp/{token}",
            headers={"Accept": "application/json, text/event-stream"},
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "save_filament_spool",
                    "arguments": {"data": {"material": "PLA"}},
                },
            },
        )
        assert denied.json()["result"]["isError"]


def test_mqtt_transport_tls_cloud_topics_and_status_only(monkeypatch):
    from types import SimpleNamespace

    import paho.mqtt.client as mqtt

    class Client:
        def __init__(self, version):
            self.requests = []
            self.subscriptions = []

        def username_pw_set(self, username, password):
            assert username == "u_123" and password == "TOKEN"

        def tls_set_context(self, context):
            assert context.check_hostname

        def connect(self, host, port, keepalive):
            assert host == "us.mqtt.bambulab.com" and port == 8883

        def subscribe(self, topics):
            self.subscriptions.extend(topics)
            self.on_subscribe(self, None, 1, [], None)

        def publish(self, topic, payload):
            self.requests.append(topic)
            assert json.loads(payload)["pushing"]["command"] == "pushall"

        def loop_start(self):
            self.on_connect(self, None, None, SimpleNamespace(is_failure=False), None)
            assert self.requests == ["device/A/request", "device/B/request"]
            assert self.subscriptions == [("device/A/report", 0), ("device/B/report", 0)]
            for serial in ("A", "B"):
                self.on_message(
                    self,
                    None,
                    SimpleNamespace(
                        topic=f"device/{serial}/report",
                        payload=json.dumps({"print": {"ams": {"ams": []}}}).encode(),
                    ),
                )

        def disconnect(self):
            pass

        def loop_stop(self):
            pass

    monkeypatch.setattr(mqtt, "Client", Client)
    assert set(mqtt_snapshot("TOKEN", "123", ["A", "B"], timeout=0)) == {"A", "B"}


def test_export_import_cloud_identity_and_backup(database, tmp_path, monkeypatch):
    session, _ = database
    service = FilamentService(session)
    source = linked(service)
    service.store("token", "PRIVATE-CLOUD-TOKEN")
    session.commit()
    payload = PortabilityService(session).export_payload()
    content = json.dumps(payload).encode()
    assert b"PRIVATE-CLOUD-TOKEN" not in content
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as fresh:
        PortabilityService(fresh).apply(content, strategy="fail")
        assert FilamentService(fresh).search()["items"][0]["cloud_id"] == "1"
        assert not FilamentService(fresh).value("token")
    csv_engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(csv_engine)
    with Session(csv_engine) as fresh:
        csv = PortabilityService(session).csv_export("filament_spools").encode()
        PortabilityService(fresh).apply(csv, strategy="fail")
        exported = FilamentService(fresh).search()["items"][0]
        assert exported["label_code"] == source["label_code"]
        assert exported["shop_code"] == "" and exported["cloud_id"] == "1"
        assert PortabilityService(fresh).apply(csv, strategy="skip").skipped == 1
    backups = BackupService(session)
    backup = backups.create_backup()
    archive = backups.archive_path(backup.filename).read_bytes()
    monkeypatch.setattr(settings, "data_dir", tmp_path / "fresh")
    target = BackupService(session)
    imported = target.import_backup(archive)
    target.schedule_restore(imported.filename)
    assert apply_pending_restore()
    with sqlite3.connect(settings.database_path) as conn:
        assert (
            conn.execute("SELECT label_code FROM filament_spools").fetchone()[0]
            == source["label_code"]
        )
        assert (
            conn.execute("SELECT value FROM system_settings WHERE key='filament.token'").fetchone()[
                0
            ]
            == "PRIVATE-CLOUD-TOKEN"
        )


def test_migration_upgrade_downgrade_and_module_choices(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "0060")
    command.upgrade(cfg, "head")
    with sqlite3.connect(settings.database_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM filament_spools").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM filament_slots").fetchone()[0] == 0
        assert conn.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "0061"
    command.downgrade(cfg, "0060")
    command.upgrade(cfg, "head")


def test_store_image_resolves_original_cloud_sku_via_official_catalog(session, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    service = FilamentService(session)
    saved = service.save(SpoolWrite(material="PLA", variant="PLA Basic", manufacturer="Bambu Lab"))
    spool = service.get(saved.id)
    spool.cloud_product_code = "A00-P6"
    session.add(spool)
    session.commit()
    picture = BytesIO()
    Image.new("RGB", (10, 10), "magenta").save(picture, format="PNG")
    calls = []

    def response(req):
        calls.append(str(req.url))
        if req.url.host == "bambu-lab-jp.myshopify.com":
            return httpx.Response(200, json={"variants": [
                {"sku": "A00-P6-1.75-1000-SPLFREE", "option1": "Magenta (10202)"},
                {"sku": "A00-P60-1.75-1000-SPL", "option1": "Other (10203)"},
            ]})
        if req.url.host == "eu.store.bambulab.com":
            product = {"hasVariant": [{"name": "PLA Basic - Magenta (10202) / Refill", "image": "https://store.bblcdn.eu/magenta.jpg"}]}
            return httpx.Response(200, text='<script id="product-jsonld">' + json.dumps(product) + '</script>')
        return httpx.Response(200, content=picture.getvalue())

    result = store_image(session, spool.id, transport=httpx.MockTransport(response))
    assert result.image_verified and result.shop_code == "10202"
    assert result.color_name == "Magenta"
    assert result.image_source_url.endswith("/de/products/pla-basic-filament")
    assert len(calls) == 3
    # Existing manual color names survive a later explicit image refresh.
    spool.color_name = "Mein Magenta"
    session.add(spool)
    session.commit()
    result = store_image(session, spool.id, transport=httpx.MockTransport(response))
    assert result.color_name == "Mein Magenta"


def test_store_cloud_sku_refuses_missing_ambiguous_or_prefix_matches():
    from app.services.filament_images import resolve_shop_code
    for variants in [[], [{"sku": "A00-P60-1.75-1000-SPL", "option1": "Wrong (10203)"}], [
        {"sku": "A00-P6-1.75-1000-SPL", "option1": "Magenta (10202)"},
        {"sku": "A00-P6-1.75-1000-SPLFREE", "option1": "Different (10203)"},
    ]]:
        with httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, json={"variants": variants}))) as client:
            with pytest.raises(ValueError):
                resolve_shop_code(client, "pla-basic-filament", "A00-P6", cache=False)
