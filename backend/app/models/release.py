from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Index, Text, event, inspect, text
from sqlalchemy.orm import Session as OrmSession
from sqlmodel import Field, SQLModel

DEFAULT_DASHBOARD_LAYOUT = json.dumps(
    [
        {"id": "documentation", "visible": True},
        {"id": "consumption_comparison", "visible": True},
        {"id": "maintenance", "visible": True},
        {"id": "quality", "visible": True},
        {"id": "network", "visible": True},
    ],
    separators=(",", ":"),
)


class DashboardSetting(SQLModel, table=True):
    __tablename__ = "dashboard_settings"

    id: int = Field(default=1, primary_key=True)
    layout_json: str = Field(default=DEFAULT_DASHBOARD_LAYOUT, sa_type=Text)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ServiceWorkload(SQLModel, table=True):
    __tablename__ = "service_workloads"
    __table_args__ = (
        CheckConstraint(
            "network_mode IN ('bridge', 'host', 'macvlan', 'docker_network')",
            name="ck_service_workloads_network_mode",
        ),
        CheckConstraint(
            "status IN ('running', 'stopped', 'planned', 'unknown')",
            name="ck_service_workloads_status",
        ),
        Index(
            "uq_service_workloads_active_host_name",
            "host_asset_id",
            "name",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    host_asset_id: UUID = Field(foreign_key="assets.id", index=True)
    name: str = Field(index=True, max_length=200)
    image: str | None = Field(default=None, max_length=500)
    image_tag: str | None = Field(default=None, max_length=200)
    compose_project: str | None = Field(default=None, index=True, max_length=200)
    network_mode: str = Field(default="bridge", index=True, max_length=30)
    macvlan_address: str | None = Field(default=None, max_length=64)
    ports_json: str = Field(default="[]", sa_type=Text)
    urls_json: str = Field(default="{}", sa_type=Text)
    reverse_proxy: str | None = Field(default=None, max_length=500)
    dependencies_json: str = Field(default="[]", sa_type=Text)
    status: str = Field(default="unknown", index=True, max_length=20)
    notes: str | None = Field(default=None, sa_type=Text)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = Field(default=None, index=True)


class AuditEvent(SQLModel, table=True):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_object", "object_type", "object_id"),
        Index("ix_audit_events_created", "created_at"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    object_type: str = Field(index=True, max_length=100)
    object_id: str = Field(index=True, max_length=100)
    action: str = Field(index=True, max_length=30)
    change_json: str = Field(sa_type=Text)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)


class GuidedSetupDraft(SQLModel, table=True):
    __tablename__ = "guided_setup_drafts"
    __table_args__ = (
        CheckConstraint(
            "current_step >= 1 AND current_step <= 11",
            name="ck_guided_setup_drafts_step",
        ),
        CheckConstraint(
            "status IN ('draft', 'applied')",
            name="ck_guided_setup_drafts_status",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=200)
    current_step: int = Field(default=1, ge=1, le=11)
    data_json: str = Field(default="{}", sa_type=Text)
    status: str = Field(default="draft", index=True, max_length=20)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


@event.listens_for(AuditEvent, "before_update")
@event.listens_for(AuditEvent, "before_delete")
def keep_audit_event_immutable(*_args: object) -> None:
    raise ValueError("Audit-Ereignisse sind unveränderlich")


_SENSITIVE_FIELDS = {
    "secret",
    "password",
    "token",
    "api_key",
    "base_url",
    "account",
    "username",
}


def _safe_change(value: object) -> object:
    if value is None or isinstance(value, bool | int | float):
        return value
    if isinstance(value, str):
        return value if len(value) <= 200 else f"{value[:197]}..."
    return str(value)


@event.listens_for(OrmSession, "before_flush")
def record_audit_events(
    session: OrmSession,
    _flush_context: object,
    _instances: object,
) -> None:
    """Capture immutable, redacted ORM history when the audit table exists."""

    bind = session.get_bind()
    if bind is None:
        return
    connection = session.connection()
    if not inspect(connection).has_table("audit_events"):
        return
    candidates = list(session.new) + list(session.dirty) + list(session.deleted)
    for record in candidates:
        if isinstance(record, AuditEvent) or not isinstance(record, SQLModel):
            continue
        state = inspect(record)
        if not state.mapper.persist_selectable.name:
            continue
        changed: dict[str, object] = {}
        action = "create" if record in session.new else "update"
        if record in session.deleted:
            action = "delete"
        for attribute in state.attrs:
            if not attribute.history.has_changes():
                continue
            key = attribute.key
            if key.casefold() in _SENSITIVE_FIELDS or any(
                marker in key.casefold() for marker in ("secret", "password", "token")
            ):
                changed[key] = "[redacted]"
                continue
            old = attribute.history.deleted[0] if attribute.history.deleted else None
            new = attribute.history.added[0] if attribute.history.added else None
            changed[key] = {"from": _safe_change(old), "to": _safe_change(new)}
            if key == "deleted_at":
                if old is None and new is not None:
                    action = "archive"
                elif old is not None and new is None:
                    action = "restore"
        if not changed and action == "update":
            continue
        record_id = getattr(record, "id", None)
        session.add(
            AuditEvent(
                object_type=state.mapper.persist_selectable.name,
                object_id=str(record_id or "pending"),
                action=action,
                change_json=json.dumps(changed, ensure_ascii=False, default=str),
            )
        )
