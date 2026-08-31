from datetime import UTC, datetime

from app.models.work import WorkItemEventPaperlessLink
from app.schemas.work import (
    RecurrenceMode,
    WorkActivityKind,
    WorkCompletionWrite,
    WorkHistoryEntryWrite,
    WorkItemType,
    WorkItemWrite,
    WorkSubjectType,
    WorkSubjectWrite,
)
from app.services.work import WorkService


def test_subject_profile_and_timeline_combine_history_and_future_due(session) -> None:
    service = WorkService(session)
    vehicle = service.create_subject(
        WorkSubjectWrite(
            name="Fahrzeug 1",
            subject_type=WorkSubjectType.VEHICLE,
            profile={
                "vehicle_kind": "PKW",
                "manufacturer": "Volkswagen",
                "license_plate": "KL-AB 123",
                "vin": "WVWTEST123",
            },
        )
    )
    inspection = service.create(
        WorkItemWrite(
            item_type=WorkItemType.MAINTENANCE,
            activity_kind=WorkActivityKind.INSPECTION,
            title="Inspektion",
            subject_id=vehicle.id,
            recurrence_mode=RecurrenceMode.INTERVAL,
            recurrence_days=365,
        )
    )
    service.complete(
        inspection.id,
        WorkCompletionWrite(
            occurred_at=datetime(2026, 2, 1, 12, tzinfo=UTC),
            note="Öl und Filter gewechselt",
            cost_amount=499.0,
            cost_currency="EUR",
            reading_value=58140,
            reading_unit="km",
        ),
    )

    timeline = service.subject_timeline(vehicle.id)

    assert timeline.subject.profile["vehicle_kind"] == "PKW"
    assert timeline.subject.profile["license_plate"] == "KL-AB 123"
    assert [entry.entry_type for entry in timeline.entries] == ["due", "history"]
    assert timeline.entries[0].title == "Inspektion"
    assert timeline.entries[0].at.date().isoformat() == "2027-02-01"
    assert timeline.entries[1].reading_value == 58140
    assert timeline.entries[1].activity_kind == WorkActivityKind.INSPECTION


def test_subject_timeline_includes_paperless_reference_without_pdf_copy(session) -> None:
    service = WorkService(session)
    penny = service.create_subject(
        WorkSubjectWrite(name="Penny", subject_type=WorkSubjectType.ANIMAL)
    )
    vaccination = service.create(
        WorkItemWrite(
            item_type=WorkItemType.MAINTENANCE,
            activity_kind=WorkActivityKind.VACCINATION,
            title="Impfung",
            subject_id=penny.id,
        )
    )
    service.add_history(
        vaccination.id,
        payload=WorkHistoryEntryWrite(
            occurred_at=datetime(2026, 4, 22, 12, tzinfo=UTC),
            note="Auffrischung",
        ),
    )
    event = service.history(vaccination.id).entries[0]
    session.add(
        WorkItemEventPaperlessLink(
            event_id=event.id,
            document_id=42,
            title="Tierarztrechnung 22.04.2026",
            created_date="2026-04-22",
            original_file_name="rechnung.pdf",
        )
    )
    session.commit()

    timeline = service.subject_timeline(penny.id)

    assert timeline.entries[0].paperless_links[0].document_id == 42
    assert timeline.entries[0].paperless_links[0].title == "Tierarztrechnung 22.04.2026"
