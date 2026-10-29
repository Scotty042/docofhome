from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.connectors.bambu import BambuCloud, BambuError, mqtt_snapshot
from app.models.asset_engine import Location
from app.models.filament import FilamentSlot, FilamentSpool
from app.models.system_setting import SystemSetting
from app.schemas.filament import CloudLogin, FilamentConfig, SpoolRead, SpoolWrite


def identity(value: Any) -> str | None:
    text = str(value or "").strip().upper()
    return text if text.strip("0") else None


def weight(value: Any) -> float | None:
    try:
        number = float(value)
        return number if 0 <= number <= 100000 else None
    except (ValueError, TypeError):
        return None


class FilamentService:
    def __init__(self, session: Session):
        self.session = session

    def value(self, key: str) -> str | None:
        row = self.session.exec(
            select(SystemSetting).where(SystemSetting.key == f"filament.{key}")
        ).first()
        return row.value if row else None

    def store(self, key: str, value: str) -> None:
        row = self.session.exec(
            select(SystemSetting).where(SystemSetting.key == f"filament.{key}")
        ).first()
        if row is None:
            row = SystemSetting(key=f"filament.{key}", value=value, is_secret=True)
        else:
            row.value = value
            row.updated_at = datetime.now(UTC)
            row.is_secret = True
        self.session.add(row)

    def config(self) -> FilamentConfig:
        try:
            return FilamentConfig.model_validate_json(self.value("config") or "{}")
        except ValueError:
            return FilamentConfig()

    def settings(self) -> dict[str, Any]:
        return {
            **self.config().model_dump(),
            "token_configured": bool(self.value("token")),
            "last_sync": self.value("last_sync"),
            "last_error": self.value("last_error"),
            "last_mqtt": self.value("last_mqtt"),
            "mqtt_error": self.value("mqtt_error"),
        }

    def save_config(self, data: FilamentConfig) -> dict[str, Any]:
        if data.enabled and (
            not self.value("token") or data.region != (self.value("region") or "global")
        ):
            raise ValueError("Zuerst für diese Region bei Bambu anmelden")
        self.store("config", data.model_dump_json())
        self.session.commit()
        return self.settings()

    def login(self, data: CloudLogin) -> dict[str, Any]:
        cloud = BambuCloud(region=data.region)
        token = data.access_token.get_secret_value() if data.access_token else None
        if not token:
            result = cloud.login(
                data.account,
                data.password.get_secret_value() if data.password else "",
                data.code.get_secret_value() if data.code else "",
            )
            token = result.get("accessToken")
            if not token:
                if result.get("loginType") == "verifyCode":
                    return {"connected": False, "verification_required": True}
                raise ValueError(
                    "Bambu-Anmeldung benötigt weitere Bestätigung; "
                    "alternativ Access Token verwenden"
                )
        cloud.token = token
        uid = cloud.uid()
        self.store("token", token)
        self.store("uid", uid)
        self.store("region", data.region)
        self.store("account", hashlib.sha256(f"{data.region}:{uid}".encode()).hexdigest())
        config = self.config().model_copy(update={"region": data.region, "enabled": False})
        self.store("config", config.model_dump_json())
        self.session.commit()
        return {"connected": True, "verification_required": False}

    def disconnect(self) -> None:
        self.store("token", "")
        self.store("uid", "")
        self.store("config", self.config().model_copy(update={"enabled": False}).model_dump_json())
        self.session.commit()

    def cloud(self) -> BambuCloud:
        if not self.value("token"):
            raise ValueError("Keine Bambu-Anmeldung gespeichert")
        return BambuCloud(self.value("token") or "", self.value("region") or "global")

    def read(self, row: FilamentSpool) -> SpoolRead:
        location = self.session.get(Location, row.location_id) if row.location_id else None
        return SpoolRead.model_validate(
            {**row.model_dump(), "location_name": location.name if location else None}
        )

    def get(self, spool_id: UUID) -> FilamentSpool:
        row = self.session.get(FilamentSpool, spool_id)
        if row is None:
            raise LookupError("Filamentrolle nicht gefunden")
        return row

    def search(
        self,
        query: str = "",
        *,
        material: str = "",
        manufacturer: str = "",
        condition: str = "",
        reorder: bool | None = None,
        archive: str = "active",
        in_ams: bool | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> dict[str, Any]:
        statement = select(FilamentSpool)
        if archive != "all":
            statement = statement.where(
                col(FilamentSpool.archived_at).is_(None)
                if archive == "active"
                else col(FilamentSpool.archived_at).is_not(None)
            )
        if query.strip():
            needle = f"%{query.strip()}%"
            statement = statement.where(
                or_(
                    *[
                        col(field).ilike(needle)
                        for field in (
                            FilamentSpool.label_code,
                            FilamentSpool.material,
                            FilamentSpool.manufacturer,
                            FilamentSpool.color_name,
                            FilamentSpool.shop_code,
                            FilamentSpool.variant,
                            FilamentSpool.rfid,
                            FilamentSpool.cloud_id,
                        )
                    ]
                )
            )
        for field, value in (
            (FilamentSpool.material, material),
            (FilamentSpool.manufacturer, manufacturer),
            (FilamentSpool.condition, condition),
        ):
            if value:
                statement = statement.where(field == value)
        if reorder is not None:
            statement = statement.where(FilamentSpool.reorder == reorder)
        if in_ams is not None:
            statement = statement.where(
                col(FilamentSpool.slot_id).is_not(None)
                if in_ams
                else col(FilamentSpool.slot_id).is_(None)
            )
        total = self.session.exec(select(func.count()).select_from(statement.subquery())).one()
        items = [
            self.read(row).model_dump(mode="json")
            for row in self.session.exec(
                statement.order_by(col(FilamentSpool.created_at).desc(), col(FilamentSpool.id))
                .offset(offset)
                .limit(limit)
            )
        ]
        return {
            "items": items,
            "total": total,
            "has_more": offset + len(items) < total,
            "next_offset": offset + len(items) if offset + len(items) < total else None,
        }

    def save(self, data: SpoolWrite, spool_id: UUID | None = None) -> SpoolRead:
        if data.location_id:
            location = self.session.get(Location, data.location_id)
            if location is None or location.deleted_at:
                raise ValueError("Lagerort nicht gefunden oder archiviert")
        row = (
            self.get(spool_id)
            if spool_id
            else FilamentSpool(id=uuid4(), label_code="", material=data.material)
        )
        if not row.label_code:
            row.label_code = "FIL-" + row.id.hex[:8].upper()
        if data.rfid:
            others = self.session.exec(
                select(FilamentSpool).where(FilamentSpool.rfid == data.rfid)
            ).all()
            if any(item.id != row.id for item in others):
                raise ValueError("Diese RFID-/Spulenkennung ist bereits einer Rolle zugeordnet")
        if row.image_url != data.image_url:
            row.image_verified = False
            row.image_source_url = None
        for key, value in data.model_dump().items():
            setattr(row, key, value)
        row.updated_at = datetime.now(UTC)
        self.session.add(row)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ValueError("Rollenkennung bereits vorhanden") from exc
        self.session.refresh(row)
        return self.read(row)

    def archive(
        self, spool_id: UUID, *, restore: bool = False, delete_cloud: bool = False
    ) -> dict[str, Any]:
        if restore and delete_cloud:
            raise ValueError("Wiederherstellen und Cloud-Löschen sind getrennte Aktionen")
        row = self.get(spool_id)
        row.archived_at = None if restore else datetime.now(UTC)
        row.updated_at = datetime.now(UTC)
        if not restore:
            row.printer_serial = row.ams_id = row.slot_id = None
            for slot in self.session.exec(
                select(FilamentSlot).where(FilamentSlot.spool_id == row.id)
            ):
                slot.spool_id = None
                slot.manual_binding = False
                self.session.add(slot)
        self.session.add(row)
        self.session.commit()
        warning = None
        if delete_cloud and not restore:
            try:
                if not row.cloud_id or row.cloud_account != self.value("account"):
                    raise ValueError("Rolle gehört nicht zum angemeldeten Cloud-Konto")
                self.cloud().delete_spool(row.cloud_id)
                row.cloud_present = False
                self.session.add(row)
                self.session.commit()
            except ValueError as exc:
                warning = "Lokal archiviert; Cloud-Löschung nicht bestätigt: " + str(exc)
        return {"item": self.read(row).model_dump(mode="json"), "warning": warning}

    def import_cloud(
        self, records: list[dict[str, Any]], *, account: str, complete: bool
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        seen: set[str] = set()
        created = updated = 0
        if any(not isinstance(data, dict) or data.get("id") is None for data in records):
            raise ValueError("Cloud-Datensatz ohne eindeutige ID; Import abgebrochen")
        for data in records:
            cloud_id = str(data["id"])
            if cloud_id in seen:
                continue
            seen.add(cloud_id)
            row = self.session.exec(
                select(FilamentSpool).where(
                    FilamentSpool.cloud_account == account, FilamentSpool.cloud_id == cloud_id
                )
            ).first()
            rfid = identity(data.get("RFID", data.get("rfid")))
            if row is None and rfid:
                matches = self.session.exec(
                    select(FilamentSpool).where(
                        FilamentSpool.rfid == rfid,
                        or_(
                            col(FilamentSpool.cloud_account) == account,
                            col(FilamentSpool.cloud_account).is_(None),
                        ),
                    )
                ).all()
                if len(matches) == 1:
                    row = matches[0]
            if row is None:
                ident = uuid4()
                hex_color = str(data.get("color") or "#808080")
                if not hex_color.startswith("#"):
                    hex_color = "#" + hex_color
                try:
                    initial = SpoolWrite(
                        material=str(
                            data.get("filamentType") or data.get("category") or "Unbekannt"
                        )[:100],
                        manufacturer=str(data.get("filamentVendor") or "")[:100],
                        variant=str(data.get("filamentName") or "")[:200],
                        color_hex=hex_color,
                    )
                except ValueError:
                    initial = SpoolWrite(material="Unbekannt")
                row = FilamentSpool(
                    id=ident, label_code="FIL-" + ident.hex[:8].upper(), **initial.model_dump()
                )
                created += 1
            else:
                updated += 1
            row.cloud_account = account
            row.cloud_id = cloud_id
            row.cloud_present = True
            row.cloud_sync_at = now
            row.rfid = row.rfid or rfid
            row.cloud_product_code = str(data.get("trayIdName") or "")[:100]
            if "netWeight" in data:
                row.remaining_g = weight(data["netWeight"])
            if row.initial_g is None:
                row.initial_g = weight(data.get("totalNetWeight"))
            if row.remaining_g is not None and row.initial_g:
                row.remaining_percent = min(100, 100 * row.remaining_g / row.initial_g)
            if row.archived_at is None and ("slotId" in data or "inPrinter" in data):
                occupied = data.get("inPrinter", True) and data.get("slotId") not in (None, "")
                if (
                    row.mount_source != "mqtt"
                    or not row.mount_observed_at
                    or now - self._aware(row.mount_observed_at) > timedelta(minutes=10)
                ):
                    row.printer_serial = str(data.get("devId") or "") or None if occupied else None
                    row.ams_id = (
                        str(data.get("amsId"))
                        if occupied and data.get("amsId") is not None
                        else None
                    )
                    row.slot_id = str(data.get("slotId")) if occupied else None
                    row.mount_source = "cloud"
                    row.mount_observed_at = now
            row.updated_at = now
            self.session.add(row)
        self.session.flush()
        if complete:
            for row in self.session.exec(
                select(FilamentSpool).where(FilamentSpool.cloud_account == account)
            ):
                if row.cloud_id not in seen:
                    row.cloud_present = False
                    self.session.add(row)
        self.session.commit()
        return {"created": created, "updated": updated, "complete": complete, "count": len(seen)}

    @staticmethod
    def _aware(value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value

    def sync(self) -> dict[str, Any]:
        try:
            snapshot = self.cloud().spools()
            result = self.import_cloud(
                snapshot["spools"],
                account=self.value("account") or "legacy",
                complete=snapshot["complete"],
            )
            self.store("last_sync", datetime.now(UTC).isoformat())
            self.store("last_error", snapshot["warning"] or "")
            self.session.commit()
            result["warning"] = snapshot["warning"]
            return result
        except ValueError as exc:
            self.session.rollback()
            self.store("last_error", str(exc))
            self.session.commit()
            raise

    def slots(self) -> list[dict[str, Any]]:
        result = []
        for slot in self.session.exec(
            select(FilamentSlot).order_by(
                FilamentSlot.printer_serial, FilamentSlot.ams_id, FilamentSlot.slot_id
            )
        ):
            spool = self.session.get(FilamentSpool, slot.spool_id) if slot.spool_id else None
            result.append(
                {**slot.model_dump(mode="json"), "spool_label": spool.label_code if spool else None}
            )
        return result

    def apply_mqtt(self, snapshots: dict[str, dict[str, Any]]) -> int:
        now = datetime.now(UTC)
        count = 0
        account = self.value("account")
        for serial, snapshot in snapshots.items():
            wrapper = snapshot.get("ams")
            if not isinstance(wrapper, dict) or not isinstance(wrapper.get("ams"), list):
                continue
            ams_list = wrapper["ams"]
            for ams in ams_list:
                if not isinstance(ams, dict) or "id" not in ams:
                    continue
                if not isinstance(ams.get("tray"), list):
                    continue
                for tray in ams.get("tray", []):
                    if not isinstance(tray, dict) or "id" not in tray:
                        continue
                    full_empty = set(tray) == {"id"} and "tray_exist_bits" in wrapper
                    if not full_empty and not any(
                        key in tray for key in ("tray_type", "tray_uuid", "tag_uid", "remain")
                    ):
                        continue
                    ams_id, slot_id = str(ams["id"]), str(tray["id"])
                    slot = self.session.exec(
                        select(FilamentSlot).where(
                            FilamentSlot.printer_serial == serial,
                            FilamentSlot.ams_id == ams_id,
                            FilamentSlot.slot_id == slot_id,
                        )
                    ).first()
                    if slot is None:
                        slot = FilamentSlot(printer_serial=serial, ams_id=ams_id, slot_id=slot_id)
                    previous = slot.spool_id
                    tag = (
                        identity(tray.get("tag_uid"))
                        if "tag_uid" in tray or full_empty
                        else slot.tag_uid
                    )
                    rfid = (
                        identity(tray.get("tray_uuid"))
                        if "tray_uuid" in tray or full_empty
                        else slot.rfid
                    )
                    if "tray_type" in tray or full_empty:
                        slot.occupied = bool(tray.get("tray_type"))
                    if slot.rfid != rfid or slot.tag_uid != tag or not slot.occupied:
                        slot.manual_binding = False
                    slot.rfid = rfid
                    slot.tag_uid = tag
                    slot.material = (
                        str(tray.get("tray_type") or "")[:100]
                        if "tray_type" in tray or full_empty
                        else slot.material
                    )
                    color = str(tray.get("tray_color") or slot.color_hex or "808080")
                    slot.color_hex = "#" + color.lstrip("#")[:8]
                    if "remain" in tray or full_empty:
                        remain = weight(tray.get("remain"))
                        slot.remaining_percent = (
                            remain if remain is not None and remain <= 100 else None
                        )
                    matches = []
                    if slot.occupied and (rfid or tag):
                        matches = list(
                            self.session.exec(
                                select(FilamentSpool).where(
                                    col(FilamentSpool.archived_at).is_(None),
                                    FilamentSpool.cloud_account == account,
                                    col(FilamentSpool.rfid).in_([v for v in (rfid, tag) if v]),
                                )
                            )
                        )
                    if not slot.occupied:
                        slot.spool_id = None
                    elif len(matches) == 1:
                        slot.spool_id = matches[0].id
                    elif not slot.manual_binding:
                        slot.spool_id = None
                    if previous and previous != slot.spool_id:
                        old = self.session.get(FilamentSpool, previous)
                        if old and (old.printer_serial, old.ams_id, old.slot_id) == (
                            serial,
                            ams_id,
                            slot_id,
                        ):
                            old.printer_serial = old.ams_id = old.slot_id = None
                            old.mount_observed_at = now
                            self.session.add(old)
                    slot.observed_at = now
                    self.session.add(slot)
                    if slot.spool_id:
                        spool = self.get(slot.spool_id)
                        if spool.archived_at is None:
                            for other in self.session.exec(
                                select(FilamentSlot).where(FilamentSlot.spool_id == spool.id)
                            ):
                                if other.id != slot.id:
                                    other.spool_id = None
                                    other.manual_binding = False
                                    self.session.add(other)
                            spool.printer_serial = serial
                            spool.ams_id = ams_id
                            spool.slot_id = slot_id
                            spool.mount_source = "mqtt"
                            spool.mount_observed_at = now
                            spool.last_seen_at = now
                            spool.remaining_percent = slot.remaining_percent
                            self.session.add(spool)
                    count += 1
        self.store("last_mqtt", now.isoformat())
        self.store("mqtt_error", "")
        self.session.commit()
        return count

    def refresh_mqtt(self) -> dict[str, Any]:
        config = self.config()
        if not config.printer_serials or not self.value("uid"):
            raise ValueError("Bambu-Anmeldung und mindestens eine Druckerkennung erforderlich")
        last = self.value("last_mqtt_request")
        if last and datetime.now(UTC) - datetime.fromisoformat(last) < timedelta(minutes=5):
            raise ValueError("AMS-Status höchstens alle fünf Minuten anfordern")
        self.store("last_mqtt_request", datetime.now(UTC).isoformat())
        self.session.commit()
        try:
            snapshots = mqtt_snapshot(
                self.value("token") or "",
                self.value("uid") or "",
                config.printer_serials,
                config.region,
            )
            return {
                "slots": self.apply_mqtt(snapshots),
                "printers_received": list(snapshots),
                "printers_missing": [v for v in config.printer_serials if v not in snapshots],
            }
        except BambuError as exc:
            self.store("mqtt_error", str(exc))
            self.session.commit()
            raise

    def bind_slot(self, slot_id: UUID, spool_id: UUID | None) -> None:
        slot = self.session.get(FilamentSlot, slot_id)
        if slot is None:
            raise LookupError("AMS-Slot nicht gefunden")
        if slot.spool_id and slot.spool_id != spool_id:
            old = self.get(slot.spool_id)
            if (old.printer_serial, old.ams_id, old.slot_id) == (
                slot.printer_serial,
                slot.ams_id,
                slot.slot_id,
            ):
                old.printer_serial = old.ams_id = old.slot_id = None
                self.session.add(old)
        if spool_id:
            spool = self.get(spool_id)
            if spool.archived_at:
                raise ValueError("Archivierte Rolle zuerst wiederherstellen")
            if not slot.occupied:
                raise ValueError("Slot wurde zuletzt leer gemeldet")
            for other in self.session.exec(
                select(FilamentSlot).where(FilamentSlot.spool_id == spool_id)
            ):
                if other.id != slot.id:
                    other.spool_id = None
                    other.manual_binding = False
                    self.session.add(other)
            spool.printer_serial = slot.printer_serial
            spool.ams_id = slot.ams_id
            spool.slot_id = slot.slot_id
            spool.mount_source = "manual"
            spool.mount_observed_at = slot.observed_at
            spool.last_seen_at = slot.observed_at
            self.session.add(spool)
        slot.spool_id = spool_id
        slot.manual_binding = spool_id is not None
        self.session.add(slot)
        self.session.commit()
