from __future__ import annotations

from datetime import UTC, date, datetime, time
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from sqlalchemy import or_
from sqlmodel import Session, select
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.settings import settings
from app.db.session import engine
from app.models.application_setting import ApplicationSetting
from app.models.recipe import Recipe
from app.schemas.asset_engine import AssetTypeWrite, AssetWrite, LabelWrite, LocationWrite, ProductWrite, SortOrder
from app.schemas.consumption import ConsumptionMeterWrite, ConsumptionNoteWrite, ConsumptionReadingWrite
from app.schemas.knowledge import KnowledgeTargetType, NoteCreate, NoteUpdate, WikiPageCreate, WikiPageUpdate
from app.schemas.mcp import McpPermission
from app.schemas.network import NetworkAddressWrite, NetworkConnectionWrite, NetworkDeviceWrite, NetworkInterfaceWrite, NetworkSegmentWrite
from app.schemas.recipe import RecipeWrite
from app.schemas.work import (
    RecurrenceMode,
    WorkCompletionWrite,
    WorkHistoryEntryWrite,
    WorkItemType,
    WorkItemWrite,
    WorkPriority,
    WorkStatus,
    WorkSubjectType,
    WorkSubjectWrite,
)
from app.services.mcp_settings import McpSettingsService
from app.services.asset_engine import AssetService, AssetTypeService, LabelService, LocationService, ProductService
from app.services.consumption import ConsumptionService
from app.services.knowledge import NoteService, WikiService
from app.services.network import NetworkService
from app.services.work import WorkConflictError, WorkService
from app.api.v1.recipes import apply as apply_recipe, read_model as read_recipe


mcp_server = MCPServer(
    "DocOfHome",
    instructions=(
        "DocOfHome verwaltet Hausdokumentation, Wissen, Rezepte, Assets, Verbrauch und Netzwerk. "
        "Bevor Daten angelegt werden, den jeweiligen Bereich nach Dubletten durchsuchen. "
        "um Dubletten zu vermeiden. Datumswerte werden als YYYY-MM-DD übergeben."
    ),
)


def _permission(session: Session, required: McpPermission) -> None:
    McpSettingsService(session).require_permission(required)


def _uuid(value: str, label: str) -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise ValueError(f"{label} ist keine gültige UUID") from exc


def _installation_zone(session: Session) -> ZoneInfo:
    application = session.get(ApplicationSetting, 1)
    name = application.timezone if application else "Europe/Berlin"
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _date_time(session: Session, value: str | None) -> datetime:
    zone = _installation_zone(session)
    if value is None:
        parsed = datetime.now(zone).date()
    else:
        try:
            parsed = date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Datum muss im Format YYYY-MM-DD angegeben werden") from exc
    local = datetime.combine(parsed, time(hour=12), tzinfo=zone)
    return local.astimezone(UTC)


def _subject_summary(subject: Any) -> dict[str, Any]:
    return {
        "id": str(subject.id),
        "name": subject.name,
        "type": subject.subject_type.value,
        "description": subject.description,
        "activity_count": subject.activity_count,
    }


def _activity_summary(activity: Any) -> dict[str, Any]:
    return {
        "id": str(activity.id),
        "title": activity.title,
        "type": activity.item_type.value,
        "status": activity.status.value,
        "subject_id": str(activity.subject_id) if activity.subject_id else None,
        "subject_name": activity.subject_name,
        "subject_type": activity.subject_type.value if activity.subject_type else None,
        "description": activity.description,
        "priority": activity.priority.value,
        "due_at": activity.due_at.isoformat() if activity.due_at else None,
        "days_remaining": activity.days_remaining,
        "recurrence_mode": activity.recurrence_mode.value,
        "recurrence_days": activity.recurrence_days,
        "calendar_months": activity.calendar_months,
        "history_count": activity.history_count,
        "last_performed_at": (
            activity.last_performed_at.isoformat() if activity.last_performed_at else None
        ),
    }


@mcp_server.tool()
def docofhome_info() -> dict[str, Any]:
    """Liefert Version, MCP-Berechtigung und grundlegende Informationen zu DocOfHome."""
    with Session(engine) as session:
        current = McpSettingsService(session).require_permission(McpPermission.READ)
        application = session.get(ApplicationSetting, 1)
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "installation_name": application.installation_name if application else None,
            "timezone": application.timezone if application else None,
            "mcp_permission": current.permission.value,
        }


@mcp_server.tool()
def search_subjects(query: str = "", subject_type: str | None = None) -> list[dict[str, Any]]:
    """Sucht Bezugsobjekte wie Tiere, Geräte, Fahrzeuge, Räume oder Installationen."""
    with Session(engine) as session:
        _permission(session, McpPermission.READ)
        subjects = WorkService(session).list_subjects()
        normalized = query.strip().casefold()
        parsed_type: WorkSubjectType | None = None
        if subject_type:
            try:
                parsed_type = WorkSubjectType(subject_type)
            except ValueError as exc:
                allowed = ", ".join(item.value for item in WorkSubjectType)
                raise ValueError(f"Unbekannter Bezugsobjekt-Typ. Erlaubt: {allowed}") from exc
        result = [
            subject
            for subject in subjects
            if (not normalized or normalized in subject.name.casefold())
            and (parsed_type is None or subject.subject_type == parsed_type)
        ]
        return [_subject_summary(subject) for subject in result[:50]]


@mcp_server.tool()
def create_subject(
    name: str,
    subject_type: str = "general",
    description: str | None = None,
) -> dict[str, Any]:
    """Legt ein neues Bezugsobjekt an. Schreibberechtigung ist erforderlich."""
    try:
        parsed_type = WorkSubjectType(subject_type)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in WorkSubjectType)
        raise ValueError(f"Unbekannter Bezugsobjekt-Typ. Erlaubt: {allowed}") from exc
    with Session(engine) as session:
        _permission(session, McpPermission.WRITE)
        subject = WorkService(session).create_subject(
            WorkSubjectWrite(name=name, subject_type=parsed_type, description=description)
        )
        return _subject_summary(subject)


@mcp_server.tool()
def update_subject(
    subject_id: str,
    name: str | None = None,
    subject_type: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Ändert Name, Typ oder Beschreibung eines Bezugsobjekts."""
    parsed_id = _uuid(subject_id, "subject_id")
    with Session(engine) as session:
        _permission(session, McpPermission.WRITE)
        service = WorkService(session)
        current = next((item for item in service.list_subjects() if item.id == parsed_id), None)
        if current is None:
            raise ValueError("Bezugsobjekt wurde nicht gefunden")
        parsed_type = current.subject_type
        if subject_type is not None:
            try:
                parsed_type = WorkSubjectType(subject_type)
            except ValueError as exc:
                allowed = ", ".join(item.value for item in WorkSubjectType)
                raise ValueError(f"Unbekannter Bezugsobjekt-Typ. Erlaubt: {allowed}") from exc
        updated = service.update_subject(
            parsed_id,
            WorkSubjectWrite(
                name=name if name is not None else current.name,
                subject_type=parsed_type,
                description=description if description is not None else current.description,
            ),
        )
        return _subject_summary(updated)


@mcp_server.tool()
def search_activities(
    query: str = "",
    subject_id: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """Sucht Tätigkeiten und Wartungen, optional innerhalb eines Bezugsobjekts."""
    with Session(engine) as session:
        _permission(session, McpPermission.READ)
        parsed_subject = _uuid(subject_id, "subject_id") if subject_id else None
        parsed_status: WorkStatus | None = None
        if status:
            try:
                parsed_status = WorkStatus(status)
            except ValueError as exc:
                allowed = ", ".join(item.value for item in WorkStatus)
                raise ValueError(f"Unbekannter Status. Erlaubt: {allowed}") from exc
        activities = WorkService(session).list(
            subject_id=parsed_subject,
            status=parsed_status,
        )
        normalized = query.strip().casefold()
        if normalized:
            activities = [
                item
                for item in activities
                if normalized in item.title.casefold()
                or (item.description and normalized in item.description.casefold())
                or (item.subject_name and normalized in item.subject_name.casefold())
            ]
        return [_activity_summary(item) for item in activities[:100]]


@mcp_server.tool()
def get_activity(activity_id: str) -> dict[str, Any]:
    """Liest eine Tätigkeit anhand ihrer ID."""
    parsed_id = _uuid(activity_id, "activity_id")
    with Session(engine) as session:
        _permission(session, McpPermission.READ)
        return _activity_summary(WorkService(session).get(parsed_id))


@mcp_server.tool()
def update_activity(
    activity_id: str,
    title: str | None = None,
    description: str | None = None,
    priority: str | None = None,
) -> dict[str, Any]:
    """Ändert Bezeichnung, Beschreibung oder Priorität einer offenen Tätigkeit."""
    parsed_id = _uuid(activity_id, "activity_id")
    with Session(engine) as session:
        _permission(session, McpPermission.WRITE)
        service = WorkService(session)
        current = service.get(parsed_id)
        parsed_priority = current.priority
        if priority is not None:
            try:
                parsed_priority = WorkPriority(priority)
            except ValueError as exc:
                raise ValueError("Priorität muss low, normal oder high sein") from exc
        updated = service.update(
            parsed_id,
            WorkItemWrite(
                item_type=current.item_type,
                title=title if title is not None else current.title,
                description=description if description is not None else current.description,
                target_type=current.target_type,
                target_id=current.target_id,
                subject_id=current.subject_id,
                due_at=current.due_at,
                recurrence_days=current.recurrence_days,
                recurrence_mode=current.recurrence_mode,
                calendar_months=current.calendar_months,
                calendar_day=current.calendar_day,
                calendar_month=current.calendar_month,
                calendar_last_day=current.calendar_last_day,
                priority=parsed_priority,
            ),
        )
        return _activity_summary(updated)


@mcp_server.tool()
def create_activity(
    subject_id: str,
    title: str,
    description: str | None = None,
    recurrence_every: int | None = None,
    recurrence_unit: str = "none",
    first_due_date: str | None = None,
    priority: str = "normal",
) -> dict[str, Any]:
    """Legt eine Tätigkeit für ein Bezugsobjekt an, optional wiederkehrend."""
    parsed_subject = _uuid(subject_id, "subject_id")
    try:
        parsed_priority = WorkPriority(priority)
    except ValueError as exc:
        raise ValueError("Priorität muss low, normal oder high sein") from exc

    unit = recurrence_unit.strip().lower()
    allowed_units = {"none", "days", "weeks", "months", "years"}
    if unit not in allowed_units:
        raise ValueError("recurrence_unit muss none, days, weeks, months oder years sein")
    if unit == "none":
        recurrence_every = None
    elif recurrence_every is None or recurrence_every < 1:
        raise ValueError("Für eine Wiederholung muss recurrence_every mindestens 1 sein")

    every = recurrence_every or 1
    recurrence_mode = RecurrenceMode.NONE
    recurrence_days: int | None = None
    calendar_months: int | None = None
    calendar_day: int | None = None
    if unit in {"days", "weeks"}:
        recurrence_mode = RecurrenceMode.INTERVAL
        recurrence_days = every * (7 if unit == "weeks" else 1)
        if recurrence_days > 3650:
            raise ValueError("Das Wiederholungsintervall darf höchstens 3650 Tage betragen")
    elif unit in {"months", "years"}:
        recurrence_mode = RecurrenceMode.CALENDAR
        calendar_months = every * (12 if unit == "years" else 1)
        if calendar_months > 120:
            raise ValueError("Das Kalenderintervall darf höchstens 120 Monate betragen")
        # The service preserves the actual performance day when calculating the next due date.
        calendar_day = 1

    with Session(engine) as session:
        _permission(session, McpPermission.WRITE)
        service = WorkService(session)
        for existing in service.list(subject_id=parsed_subject):
            if existing.title.casefold() == title.strip().casefold():
                raise WorkConflictError(
                    "Für dieses Bezugsobjekt existiert bereits eine Tätigkeit mit diesem Titel"
                )
        due_at = _date_time(session, first_due_date) if first_due_date else None
        created = service.create(
            WorkItemWrite(
                item_type=WorkItemType.MAINTENANCE,
                title=title,
                description=description,
                subject_id=parsed_subject,
                due_at=due_at,
                recurrence_days=recurrence_days,
                recurrence_mode=recurrence_mode,
                calendar_months=calendar_months,
                calendar_day=calendar_day,
                calendar_month=None,
                calendar_last_day=False,
                priority=parsed_priority,
            )
        )
        return _activity_summary(created)


@mcp_server.tool()
def log_activity(
    activity_id: str,
    performed_date: str | None = None,
    note: str | None = None,
    cost_amount: float | None = None,
    cost_currency: str = "EUR",
    reading_value: float | None = None,
    reading_unit: str | None = None,
) -> dict[str, Any]:
    """Protokolliert eine aktuelle Durchführung und berechnet die nächste Fälligkeit neu.

    Ohne Datum wird der heutige Tag verwendet. Für reine rückwirkende Nachpflege, die
    den aktuellen Fälligkeitstermin nicht verändern soll, add_history_entry verwenden.
    """
    parsed_id = _uuid(activity_id, "activity_id")
    with Session(engine) as session:
        _permission(session, McpPermission.WRITE)
        service = WorkService(session)
        activity = service.get(parsed_id)
        occurred_at = _date_time(session, performed_date)
        payload = WorkCompletionWrite(
            occurred_at=occurred_at,
            note=note,
            cost_amount=cost_amount,
            cost_currency=cost_currency,
            reading_value=reading_value,
            reading_unit=reading_unit,
        )
        if activity.status == WorkStatus.OPEN:
            updated = service.complete(parsed_id, payload)
        elif activity.status == WorkStatus.COMPLETED:
            service.add_history(
                parsed_id,
                WorkHistoryEntryWrite(
                    **payload.model_dump(exclude={"occurred_at"}),
                    occurred_at=occurred_at,
                ),
            )
            updated = service.get(parsed_id)
        else:
            raise WorkConflictError("Eine abgebrochene Tätigkeit kann nicht protokolliert werden")
        return _activity_summary(updated)


@mcp_server.tool()
def add_history_entry(
    activity_id: str,
    performed_date: str,
    note: str | None = None,
    cost_amount: float | None = None,
    cost_currency: str = "EUR",
    reading_value: float | None = None,
    reading_unit: str | None = None,
) -> dict[str, Any]:
    """Ergänzt einen historischen Durchführungstermin.

    Die nächste Fälligkeit bleibt dabei unverändert.
    """
    parsed_id = _uuid(activity_id, "activity_id")
    with Session(engine) as session:
        _permission(session, McpPermission.WRITE)
        service = WorkService(session)
        occurred_at = _date_time(session, performed_date)
        entry = service.add_history(
            parsed_id,
            WorkHistoryEntryWrite(
                occurred_at=occurred_at,
                note=note,
                cost_amount=cost_amount,
                cost_currency=cost_currency,
                reading_value=reading_value,
                reading_unit=reading_unit,
            ),
        )
        return entry.model_dump(mode="json")


@mcp_server.tool()
def get_activity_history(activity_id: str) -> dict[str, Any]:
    """Liest die vollständige Durchführungshistorie einer Tätigkeit samt Intervallen."""
    parsed_id = _uuid(activity_id, "activity_id")
    with Session(engine) as session:
        _permission(session, McpPermission.READ)
        history = WorkService(session).history(parsed_id)
        return history.model_dump(mode="json")


@mcp_server.tool()
def get_due_activities(days: int = 31) -> list[dict[str, Any]]:
    """Liefert überfällige und innerhalb der nächsten Tage fällige Tätigkeiten."""
    if days < 0 or days > 365:
        raise ValueError("days muss zwischen 0 und 365 liegen")
    with Session(engine) as session:
        _permission(session, McpPermission.READ)
        activities = WorkService(session).list(status=WorkStatus.OPEN)
        result = [
            item
            for item in activities
            if item.days_remaining is not None and item.days_remaining <= days
        ]
        return [_activity_summary(item) for item in result[:100]]


@mcp_server.tool()
def delete_history_entry(activity_id: str, event_id: str) -> dict[str, str]:
    """Löscht einen historischen Eintrag. Vollzugriff (admin) ist erforderlich."""
    parsed_activity = _uuid(activity_id, "activity_id")
    parsed_event = _uuid(event_id, "event_id")
    with Session(engine) as session:
        _permission(session, McpPermission.ADMIN)
        WorkService(session).delete_history(parsed_activity, parsed_event)
        return {"status": "deleted", "event_id": str(parsed_event)}


@mcp_server.tool()
def delete_activity(activity_id: str) -> dict[str, str]:
    """Archiviert/löscht eine Tätigkeit. Vollzugriff (admin) ist erforderlich."""
    parsed_id = _uuid(activity_id, "activity_id")
    with Session(engine) as session:
        _permission(session, McpPermission.ADMIN)
        WorkService(session).delete(parsed_id)
        return {"status": "deleted", "activity_id": str(parsed_id)}


@mcp_server.tool()
def delete_subject(subject_id: str) -> dict[str, str]:
    """Löscht ein unbenutztes Bezugsobjekt. Vollzugriff (admin) ist erforderlich."""
    parsed_id = _uuid(subject_id, "subject_id")
    with Session(engine) as session:
        _permission(session, McpPermission.ADMIN)
        WorkService(session).delete_subject(parsed_id)
        return {"status": "deleted", "subject_id": str(parsed_id)}


# Knowledge and cookbook
@mcp_server.tool()
def search_recipes(query: str = "", category: str = "", tag: str = "") -> list[dict[str, Any]]:
    """Sucht Rezepte nach Titel/Zutat sowie optional Kategorie und Tag."""
    with Session(engine) as session:
        _permission(session, McpPermission.READ)
        statement = select(Recipe)
        if query.strip():
            needle = f"%{query.strip()}%"
            statement = statement.where(or_(Recipe.title.ilike(needle), Recipe.ingredients_json.ilike(needle)))
        if category.strip(): statement = statement.where(Recipe.category == category.strip())
        if tag.strip(): statement = statement.where(Recipe.tags_json.ilike(f'%"{tag.strip()}"%'))
        return [read_recipe(row).model_dump(mode="json") for row in session.exec(statement.order_by(Recipe.favorite.desc(), Recipe.title)).all()[:100]]


@mcp_server.tool()
def get_recipe(recipe_id: str) -> dict[str, Any]:
    """Liest ein vollständiges Rezept einschließlich Zutaten und Schritten."""
    with Session(engine) as session:
        _permission(session, McpPermission.READ)
        row = session.get(Recipe, _uuid(recipe_id, "recipe_id"))
        if row is None: raise ValueError("Rezept wurde nicht gefunden")
        return read_recipe(row).model_dump(mode="json")


@mcp_server.tool()
def save_recipe(payload: dict[str, Any], recipe_id: str | None = None) -> dict[str, Any]:
    """Legt ein Rezept an oder ersetzt es vollständig. payload entspricht RecipeWrite."""
    data = RecipeWrite.model_validate(payload)
    with Session(engine) as session:
        _permission(session, McpPermission.WRITE)
        row = session.get(Recipe, _uuid(recipe_id, "recipe_id")) if recipe_id else Recipe(title=data.title)
        if row is None: raise ValueError("Rezept wurde nicht gefunden")
        apply_recipe(row, data); session.add(row); session.commit(); session.refresh(row)
        return read_recipe(row).model_dump(mode="json")


@mcp_server.tool()
def delete_recipe(recipe_id: str) -> dict[str, str]:
    """Löscht ein Rezept. Vollzugriff ist erforderlich."""
    with Session(engine) as session:
        _permission(session, McpPermission.ADMIN)
        row = session.get(Recipe, _uuid(recipe_id, "recipe_id"))
        if row is None: raise ValueError("Rezept wurde nicht gefunden")
        session.delete(row); session.commit(); return {"status": "deleted", "recipe_id": recipe_id}


@mcp_server.tool()
def search_wiki(query: str = "") -> list[dict[str, Any]]:
    """Sucht Wiki-Seiten in Titel, Pfad und Inhalt."""
    with Session(engine) as session:
        _permission(session, McpPermission.READ)
        return [item.model_dump(mode="json") for item in WikiService(session).list(search=query)]


@mcp_server.tool()
def get_wiki_page(page_id: str) -> dict[str, Any]:
    """Liest eine Wiki-Seite vollständig."""
    with Session(engine) as session:
        _permission(session, McpPermission.READ)
        return WikiService(session).get(_uuid(page_id, "page_id")).model_dump(mode="json")


@mcp_server.tool()
def save_wiki_page(payload: dict[str, Any], page_id: str | None = None) -> dict[str, Any]:
    """Legt eine Wiki-Seite an oder ersetzt sie vollständig."""
    with Session(engine) as session:
        _permission(session, McpPermission.WRITE); service = WikiService(session)
        result = service.update(_uuid(page_id, "page_id"), WikiPageUpdate.model_validate(payload)) if page_id else service.create(WikiPageCreate.model_validate(payload))
        return result.model_dump(mode="json")


@mcp_server.tool()
def delete_wiki_page(page_id: str) -> dict[str, str]:
    """Archiviert eine Wiki-Seite ohne aktive Unterseiten. Vollzugriff erforderlich."""
    with Session(engine) as session:
        _permission(session, McpPermission.ADMIN); WikiService(session).archive(_uuid(page_id, "page_id")); return {"status": "archived", "page_id": page_id}


@mcp_server.tool()
def list_notes(target_type: str, target_id: str) -> list[dict[str, Any]]:
    """Liest Notizen eines Assets, Orts oder Elektroobjekts."""
    with Session(engine) as session:
        _permission(session, McpPermission.READ)
        return [item.model_dump(mode="json") for item in NoteService(session).list(KnowledgeTargetType(target_type), _uuid(target_id, "target_id"))]


@mcp_server.tool()
def save_note(content: str, target_type: str | None = None, target_id: str | None = None, note_id: str | None = None) -> dict[str, Any]:
    """Legt eine verknüpfte Notiz an oder ändert ihren Inhalt."""
    with Session(engine) as session:
        _permission(session, McpPermission.WRITE); service = NoteService(session)
        if note_id: result = service.update(_uuid(note_id, "note_id"), NoteUpdate(content=content))
        else:
            if not target_type or not target_id: raise ValueError("target_type und target_id sind beim Anlegen erforderlich")
            result = service.create(NoteCreate(target_type=KnowledgeTargetType(target_type), target_id=_uuid(target_id, "target_id"), content=content))
        return result.model_dump(mode="json")


@mcp_server.tool()
def delete_note(note_id: str) -> dict[str, str]:
    """Löscht eine Notiz. Vollzugriff erforderlich."""
    with Session(engine) as session:
        _permission(session, McpPermission.ADMIN); NoteService(session).delete(_uuid(note_id, "note_id")); return {"status": "deleted", "note_id": note_id}


# Assets, locations and master data
def _catalog_service(session: Session, domain: str) -> Any:
    services = {"asset": AssetService, "location": LocationService, "asset_type": AssetTypeService, "product": ProductService, "label": LabelService}
    if domain not in services: raise ValueError("domain muss asset, location, asset_type, product oder label sein")
    return services[domain](session)


@mcp_server.tool()
def search_catalog(domain: str, query: str = "") -> dict[str, Any]:
    """Sucht Assets, Orte, Assettypen, Produkte oder Labels."""
    with Session(engine) as session:
        _permission(session, McpPermission.READ); service = _catalog_service(session, domain)
        common = dict(page=1, page_size=100, search=query or None, sort_by="name", sort_order=SortOrder.ASC, include_deleted=False)
        if domain == "asset": page = service.list_read(**common, filters={}, label_id=None)
        elif domain == "location": page = service.list_read(**common, parent_id=None, location_type=None)
        else: page = service.list(**common)
        return page.model_dump(mode="json")


@mcp_server.tool()
def get_catalog_record(domain: str, record_id: str) -> dict[str, Any]:
    """Liest einen Datensatz aus Assets, Orten oder Stammdaten."""
    with Session(engine) as session:
        _permission(session, McpPermission.READ); service = _catalog_service(session, domain); identifier = _uuid(record_id, "record_id")
        result = service.get_read(identifier) if domain in {"asset", "location"} else service.get(identifier)
        return result.model_dump(mode="json")


@mcp_server.tool()
def save_catalog_record(domain: str, payload: dict[str, Any], record_id: str | None = None) -> dict[str, Any]:
    """Legt ein Asset, einen Ort oder Stammdatensatz an bzw. ersetzt ihn vollständig."""
    schemas = {"asset": AssetWrite, "location": LocationWrite, "asset_type": AssetTypeWrite, "product": ProductWrite, "label": LabelWrite}
    if domain not in schemas: raise ValueError("Unbekannter domain-Wert")
    data = schemas[domain].model_validate(payload)
    with Session(engine) as session:
        _permission(session, McpPermission.WRITE); service = _catalog_service(session, domain)
        result = service.update(_uuid(record_id, "record_id"), data) if record_id else service.create(data)
        return result.model_dump(mode="json")


@mcp_server.tool()
def delete_catalog_record(domain: str, record_id: str) -> dict[str, str]:
    """Archiviert ein Asset, einen Ort oder Stammdatensatz. Vollzugriff erforderlich."""
    with Session(engine) as session:
        _permission(session, McpPermission.ADMIN); _catalog_service(session, domain).delete(_uuid(record_id, "record_id")); return {"status": "archived", "domain": domain, "record_id": record_id}


# Consumption
@mcp_server.tool()
def list_consumption(kind: str, meter_id: str | None = None, query: str = "", months: int = 12, days_ahead: int = 3) -> Any:
    """Liest summary, statistics, reminder, meter, reading oder note aus Verbrauch."""
    with Session(engine) as session:
        _permission(session, McpPermission.READ); service = ConsumptionService(session)
        if kind == "summary": return service.summary().model_dump(mode="json")
        if kind == "statistics": return service.statistics(months=months).model_dump(mode="json")
        if kind == "reminder": return [item.model_dump(mode="json") for item in service.reading_reminders(days_ahead=days_ahead)]
        if kind == "meter": return [item.model_dump(mode="json") for item in service.list_meters(search=query or None)]
        if kind == "reading": return [item.model_dump(mode="json") for item in service.list_readings(meter_id=_uuid(meter_id, "meter_id") if meter_id else None)]
        if kind == "note": return [item.model_dump(mode="json") for item in service.list_notes()]
        raise ValueError("Unbekannter kind-Wert")


@mcp_server.tool()
def save_consumption_record(kind: str, payload: dict[str, Any], record_id: str | None = None) -> dict[str, Any]:
    """Legt einen Zähler/eine Ablesung an oder ersetzt den Datensatz vollständig."""
    with Session(engine) as session:
        _permission(session, McpPermission.WRITE); service = ConsumptionService(session)
        if kind == "meter": result = service.update_meter(_uuid(record_id, "record_id"), ConsumptionMeterWrite.model_validate(payload)) if record_id else service.create_meter(ConsumptionMeterWrite.model_validate(payload))
        elif kind == "reading": result = service.update_reading(_uuid(record_id, "record_id"), ConsumptionReadingWrite.model_validate(payload)) if record_id else service.create_reading(ConsumptionReadingWrite.model_validate(payload))
        elif kind == "note": result = service.update_note(_uuid(record_id, "record_id"), ConsumptionNoteWrite.model_validate(payload)) if record_id else service.create_note(ConsumptionNoteWrite.model_validate(payload))
        else: raise ValueError("kind muss meter, reading oder note sein")
        return result.model_dump(mode="json")


@mcp_server.tool()
def delete_consumption_record(kind: str, record_id: str) -> dict[str, str]:
    """Archiviert einen Zähler oder eine Ablesung. Vollzugriff erforderlich."""
    with Session(engine) as session:
        _permission(session, McpPermission.ADMIN); service = ConsumptionService(session); identifier = _uuid(record_id, "record_id")
        if kind == "meter": service.archive_meter(identifier)
        elif kind == "reading": service.archive_reading(identifier)
        elif kind == "note": service.archive_note(identifier)
        else: raise ValueError("kind muss meter, reading oder note sein")
        return {"status": "archived", "kind": kind, "record_id": record_id}


# Network
def _network_schema(kind: str) -> Any:
    schemas = {"device": NetworkDeviceWrite, "segment": NetworkSegmentWrite, "interface": NetworkInterfaceWrite, "address": NetworkAddressWrite, "connection": NetworkConnectionWrite}
    if kind not in schemas: raise ValueError("kind muss device, segment, interface, address oder connection sein")
    return schemas[kind]


@mcp_server.tool()
def list_network(kind: str, device_id: str | None = None, query: str = "") -> list[dict[str, Any]]:
    """Liest Netzwerkgeräte, Segmente, Schnittstellen, Adressen oder Verbindungen."""
    with Session(engine) as session:
        _permission(session, McpPermission.READ); service = NetworkService(session); device = _uuid(device_id, "device_id") if device_id else None
        if kind == "summary": return [service.summary().model_dump(mode="json")]
        if kind == "topology": return [service.topology().model_dump(mode="json")]
        if kind == "device": items = service.list_devices(search=query or None)
        elif kind == "segment": items = service.list_segments()
        elif kind == "interface": items = service.list_interfaces(device_id=device)
        elif kind == "address": items = service.list_addresses(device_id=device)
        elif kind == "connection": items = service.list_connections(device_id=device)
        else: raise ValueError("Unbekannter kind-Wert")
        return [item.model_dump(mode="json") for item in items]


@mcp_server.tool()
def save_network_record(kind: str, payload: dict[str, Any], record_id: str | None = None) -> dict[str, Any]:
    """Legt einen Netzwerkdatensatz an oder ersetzt ihn vollständig."""
    data = _network_schema(kind).model_validate(payload); identifier = _uuid(record_id, "record_id") if record_id else None
    with Session(engine) as session:
        _permission(session, McpPermission.WRITE); service = NetworkService(session)
        create = {"device": service.create_device, "segment": service.create_segment, "interface": service.create_interface, "address": service.create_address, "connection": service.create_connection}[kind]
        update = {"device": service.update_device, "segment": service.update_segment, "interface": service.update_interface, "address": service.update_address, "connection": service.update_connection}[kind]
        return (update(identifier, data) if identifier else create(data)).model_dump(mode="json")


@mcp_server.tool()
def delete_network_record(kind: str, record_id: str) -> dict[str, str]:
    """Archiviert einen Netzwerkdatensatz. Vollzugriff erforderlich."""
    with Session(engine) as session:
        _permission(session, McpPermission.ADMIN); service = NetworkService(session)
        delete = {"device": service.delete_device, "segment": service.delete_segment, "interface": service.delete_interface, "address": service.delete_address, "connection": service.delete_connection}.get(kind)
        if delete is None: raise ValueError("Unbekannter kind-Wert")
        delete(_uuid(record_id, "record_id")); return {"status": "archived", "kind": kind, "record_id": record_id}


class McpBearerAuthMiddleware:
    """Small ASGI bearer gate backed by the persistent DocOfHome MCP token.

    A plain ASGI wrapper is used deliberately instead of BaseHTTPMiddleware so
    Streamable HTTP response bodies are not buffered or disconnected.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        raw_header = headers.get(b"authorization", b"").decode("latin-1")
        bearer_token = raw_header[7:].strip() if raw_header.lower().startswith("bearer ") else ""
        path = scope.get("path", "")
        path_token = path.removeprefix("/mcp/") if path.startswith("/mcp/") else ""
        token = bearer_token or path_token
        with Session(engine) as session:
            mcp_settings = McpSettingsService(session)
            current = mcp_settings.read()
            if not current.enabled:
                response = JSONResponse({"detail": "MCP ist deaktiviert"}, status_code=404)
                await response(scope, receive, send)
                return
            if not token or not mcp_settings.verify_token(token):
                response = JSONResponse(
                    {"detail": "Ungültiger oder fehlender MCP-Token"},
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer"},
                )
                await response(scope, receive, send)
                return

        # The MCP SDK is intentionally configured for one canonical endpoint.
        # Token-in-path requests are authenticated above, then dispatched to the
        # exact same /mcp ASGI application as bearer requests.
        if path_token:
            scope = {**scope, "path": "/mcp", "raw_path": b"/mcp"}
        await self.app(scope, receive, send)


# The public hostname is user-configurable at runtime and is normally terminated by SWAG.
# Host filtering therefore belongs to the reverse proxy. The MCP endpoint itself remains
# protected by the application-level bearer token even when this SDK protection is off.
_transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)
_raw_mcp_app = mcp_server.streamable_http_app(
    streamable_http_path="/mcp",
    stateless_http=True,
    json_response=True,
    transport_security=_transport_security,
)
mcp_http_app: ASGIApp = McpBearerAuthMiddleware(_raw_mcp_app)
