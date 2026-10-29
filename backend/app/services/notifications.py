from __future__ import annotations

import hashlib
import re
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from sqlalchemy import delete, or_, update
from sqlalchemy.dialects.sqlite import insert
from sqlmodel import Session, col, select

from app.models.application_setting import ApplicationSetting
from app.models.notifications import PushDelivery
from app.models.system_setting import SystemSetting
from app.models.work import WorkItem
from app.schemas.notifications import Provider, PushConfig, PushDeliveryRead, PushRead, PushWrite
from app.services.consumption import ConsumptionService

CONFIG_KEY = "push.config"
SECRET_FIELDS = ("pushover_app_token", "pushover_user_key", "ntfy_access_token")


class PushError(ValueError):
    pass


class PushService:
    def __init__(self, session: Session, *, transport: httpx.BaseTransport | None = None):
        self.session = session
        self.transport = transport

    def _stored(self, key: str) -> str | None:
        row = self.session.exec(select(SystemSetting).where(SystemSetting.key == key)).first()
        return row.value if row else None

    def _write(self, key: str, value: str) -> None:
        row = self.session.exec(select(SystemSetting).where(SystemSetting.key == key)).first()
        if row is None:
            row = SystemSetting(key=key, value=value, is_secret=True)
        else:
            row.value = value
            row.is_secret = True
            row.updated_at = datetime.now(UTC)
        self.session.add(row)

    def configuration(self) -> PushConfig:
        try:
            return PushConfig.model_validate_json(self._stored(CONFIG_KEY) or "{}")
        except ValueError:
            # A malformed configuration must never start outbound traffic.
            return PushConfig()

    def read(self) -> PushRead:
        return PushRead(
            **self.configuration().model_dump(),
            **{f"{key}_configured": bool(self._stored(f"push.{key}")) for key in SECRET_FIELDS},
        )

    def effective(self, payload: PushWrite) -> tuple[PushConfig, dict[str, str]]:
        config = PushConfig.model_validate(payload.model_dump(include=set(PushConfig.model_fields)))
        secrets: dict[str, str] = {}
        for key in SECRET_FIELDS:
            value = getattr(payload, key)
            clear = getattr(payload, f"clear_{key}")
            if clear and value is not None:
                raise PushError("Schlüssel entweder ersetzen oder entfernen")
            secrets[key] = (
                ""
                if clear
                else value.get_secret_value()
                if value
                else self._stored(f"push.{key}") or ""
            )
        return config, secrets

    @staticmethod
    def validate_provider(provider: Provider, config: PushConfig, secrets: dict[str, str]) -> None:
        if provider == "pushover":
            if not all(
                re.fullmatch(r"[A-Za-z0-9]{30}", secrets[key])
                for key in ("pushover_app_token", "pushover_user_key")
            ):
                raise PushError(
                    "Pushover benötigt App-Token und Benutzer-/Gruppenschlüssel (je 30 Zeichen)"
                )
        elif not config.ntfy_topic:
            raise PushError("Für ntfy ein Topic angeben")

    def save(self, payload: PushWrite) -> PushRead:
        config, secrets = self.effective(payload)
        if config.enabled and not (config.pushover_enabled or config.ntfy_enabled):
            raise PushError("Mindestens einen Push-Dienst aktivieren")
        if config.enabled and not any(
            (config.readings_enabled, config.maintenance_enabled, config.tasks_enabled)
        ):
            raise PushError("Mindestens eine Erinnerungskategorie aktivieren")
        for provider in ("pushover", "ntfy"):
            if config.enabled and getattr(config, f"{provider}_enabled"):
                self.validate_provider(provider, config, secrets)
        # Config includes potentially private ntfy topics; exclude it from portable exports too.
        self._write(CONFIG_KEY, config.model_dump_json())
        for key, value in secrets.items():
            self._write(f"push.{key}", value)
        self.session.commit()
        return self.read()

    def history(self) -> list[PushDeliveryRead]:
        rows = self.session.exec(
            select(PushDelivery).order_by(col(PushDelivery.created_at).desc()).limit(20)
        )
        return [PushDeliveryRead.model_validate(row.model_dump()) for row in rows]

    def _send(
        self,
        provider: Provider,
        config: PushConfig,
        secrets: dict[str, str],
        title: str,
        message: str,
        route: str,
    ) -> None:
        self.validate_provider(provider, config, secrets)
        link = f"{config.public_url}{route}" if config.public_url else None
        try:
            with httpx.Client(
                timeout=10, follow_redirects=False, trust_env=False, transport=self.transport
            ) as client:
                if provider == "pushover":
                    payload = {
                        "token": secrets["pushover_app_token"],
                        "user": secrets["pushover_user_key"],
                        "title": title,
                        "message": message,
                        "priority": "0",
                    }
                    if config.pushover_device:
                        payload["device"] = config.pushover_device
                    if link:
                        payload.update(url=link, url_title="In DocOfHome öffnen")
                    response = client.post("https://api.pushover.net/1/messages.json", data=payload)
                    body = response.json() if response.is_success else None
                    accepted = isinstance(body, dict) and body.get("status") == 1
                else:
                    data: dict[str, Any] = {
                        "topic": config.ntfy_topic,
                        "title": title,
                        "message": message,
                        "priority": 3,
                    }
                    if link:
                        data["click"] = link
                    headers = (
                        {"Authorization": f"Bearer {secrets['ntfy_access_token']}"}
                        if secrets["ntfy_access_token"]
                        else {}
                    )
                    response = client.post(f"{config.ntfy_url}/", json=data, headers=headers)
                    body = response.json() if response.is_success else None
                    accepted = isinstance(body, dict) and bool(body.get("id"))
                if not accepted:
                    raise PushError(
                        f"{provider}: Nachricht nicht bestätigt (HTTP {response.status_code})"
                    )
        except (httpx.HTTPError, ValueError) as exc:
            if isinstance(exc, PushError):
                raise
            # Never propagate provider bodies, URLs or exception text containing credentials.
            raise PushError(f"{provider}: Verbindung oder Antwort fehlerhaft") from None

    def _claim(
        self, key: str, provider: Provider, now: datetime, kind: str = "daily"
    ) -> PushDelivery | None:
        self.session.execute(
            insert(PushDelivery)
            .values(
                id=uuid4(),
                delivery_key=key,
                provider=provider,
                kind=kind,
                status="pending",
                attempts=0,
                created_at=now,
            )
            .on_conflict_do_nothing(index_elements=["delivery_key"])
        )
        self.session.commit()
        claimed = self.session.execute(
            update(PushDelivery)
            .where(
                col(PushDelivery.delivery_key) == key,
                col(PushDelivery.status) != "sent",
                col(PushDelivery.attempts) < 3,
                or_(col(PushDelivery.status) == "pending", col(PushDelivery.next_retry_at) <= now),
            )
            .values(
                status="sending",
                attempts=col(PushDelivery.attempts) + 1,
                last_attempt_at=now,
                next_retry_at=now + timedelta(minutes=15),
                detail=None,
            )
        )
        changed = getattr(claimed, "rowcount", 0)
        self.session.commit()
        if changed != 1:
            return None
        return self.session.exec(select(PushDelivery).where(PushDelivery.delivery_key == key)).one()

    def _deliver(
        self,
        row: PushDelivery,
        provider: Provider,
        config: PushConfig,
        secrets: dict[str, str],
        message: str,
        route: str,
    ) -> bool:
        try:
            self._send(
                provider,
                config,
                secrets,
                "DocOfHome · Erinnerungen" if row.kind == "daily" else "DocOfHome · Testnachricht",
                message,
                route,
            )
            row.status = "sent"
            row.detail = "Vom Push-Dienst angenommen"
            row.next_retry_at = None
            success = True
        except PushError as exc:
            row.status = "failed"
            row.detail = str(exc)
            if row.kind == "test" or row.attempts >= 3:
                row.next_retry_at = None
            success = False
        self.session.add(row)
        self.session.commit()
        return success

    def test(self, provider: Provider, payload: PushWrite) -> bool:
        config, secrets = self.effective(payload)
        self.validate_provider(provider, config, secrets)
        row = self._claim(f"test:{uuid4()}", provider, datetime.now(UTC), "test")
        if row is None:
            raise PushError("Test konnte nicht gestartet werden")
        return self._deliver(
            row, provider, config, secrets, "Die Push-Verbindung zu DocOfHome funktioniert.", "/"
        )

    def _zone(self) -> ZoneInfo:
        application = self.session.get(ApplicationSetting, 1)
        try:
            return ZoneInfo(application.timezone if application else "Europe/Berlin")
        except ZoneInfoNotFoundError:
            return ZoneInfo("UTC")

    def digest(self, config: PushConfig, today: date) -> tuple[str, str] | None:
        entries: list[tuple[date, str, str]] = []
        zone = self._zone()
        if config.readings_enabled:
            for reminder in ConsumptionService(self.session).reading_reminders(
                days_ahead=config.days_ahead, _today=today
            ):
                entries.append(
                    (
                        reminder.due_at.astimezone(zone).date(),
                        f"Zähler ablesen: {reminder.meter_name}",
                        "reading",
                    )
                )
        if config.tasks_enabled or config.maintenance_enabled:
            for item in self.session.exec(
                select(WorkItem).where(
                    col(WorkItem.deleted_at).is_(None),
                    WorkItem.status == "open",
                    col(WorkItem.due_at).is_not(None),
                )
            ):
                if item.automation_key and item.automation_key.startswith("meter-reading:"):
                    continue
                if not (
                    config.maintenance_enabled
                    if item.item_type == "maintenance"
                    else config.tasks_enabled
                ):
                    continue
                assert item.due_at is not None
                due = item.due_at.replace(tzinfo=UTC) if item.due_at.tzinfo is None else item.due_at
                local_due = due.astimezone(zone).date()
                if (local_due - today).days <= config.days_ahead:
                    label = "Wartung" if item.item_type == "maintenance" else "Aufgabe"
                    title = f"{item.title} ({label})"
                    entries.append((local_due, title, "work"))
        if not entries:
            return None
        entries.sort(key=lambda e: (e[0], e[1]))
        lines = [f"{len(entries)} offene Erinnerungen · {today:%d.%m.%Y}"]
        shown = 0
        for due_date, title, _kind in entries:
            suffix = (
                "überfällig"
                if due_date < today
                else "heute"
                if due_date == today
                else due_date.strftime("%d.%m.%Y")
            )
            line = f"• {title[:160]} – {suffix}"
            if len("\n".join([*lines, line])) > 820:
                break
            lines.append(line)
            shown += 1
        if shown < len(entries):
            lines.append(f"… und {len(entries) - shown} weitere. Details in DocOfHome.")
        route = (
            "/consumption"
            if all(e[2] == "reading" for e in entries)
            else "/maintenance"
            if all(e[2] == "work" for e in entries)
            else "/"
        )
        return "\n".join(lines), route

    def run_once(self, *, now: datetime | None = None) -> int:
        config = self.configuration()
        if not config.enabled:
            return 0
        now = (now or datetime.now(UTC)).astimezone(UTC)
        local = now.astimezone(self._zone())
        if (local.hour, local.minute) < (config.send_hour, config.send_minute):
            return 0
        digest = self.digest(config, local.date())
        if digest is None:
            return 0
        secrets = {key: self._stored(f"push.{key}") or "" for key in SECRET_FIELDS}
        count = 0
        for provider in ("pushover", "ntfy"):
            if not getattr(config, f"{provider}_enabled"):
                continue
            destination = (
                secrets["pushover_user_key"] + config.pushover_device
                if provider == "pushover"
                else f"{config.ntfy_url}/{config.ntfy_topic}"
            )
            fingerprint = hashlib.sha256(destination.encode()).hexdigest()[:24]
            key = f"daily:{local.date()}:{provider}:{fingerprint}"
            row = self._claim(key, provider, now)
            if row is not None:
                count += int(self._deliver(row, provider, config, secrets, *digest))
        self.session.execute(
            delete(PushDelivery).where(col(PushDelivery.created_at) < now - timedelta(days=90))
        )
        self.session.commit()
        return count
