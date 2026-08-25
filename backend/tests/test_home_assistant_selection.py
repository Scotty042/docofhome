from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine

from app.models.asset_engine import Asset, AssetType
from app.models.home_assistant import (
    HomeAssistantEntitySelection,
    HomeAssistantSelectionSetting,
)
from app.schemas.home_assistant import (
    HomeAssistantObjectType,
    HomeAssistantSelectionMode,
    HomeAssistantSelectionWrite,
)
from app.services.home_assistant_links import HomeAssistantLinkService
from app.services.home_assistant_selection import (
    HomeAssistantSelectionError,
    HomeAssistantSelectionService,
)


def selection_engine():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return engine


def test_selection_defaults_to_all_and_replaces_atomically_across_sessions() -> None:
    engine = selection_engine()
    with Session(engine) as session:
        service = HomeAssistantSelectionService(session)
        assert service.get().mode == HomeAssistantSelectionMode.ALL
        assert service.get().entity_ids == []

        stored = service.replace(
            HomeAssistantSelectionWrite(
                mode=HomeAssistantSelectionMode.SELECTED,
                entity_ids=[
                    " sensor.grid_power ",
                    "light.kitchen",
                    "sensor.grid_power",
                ],
            )
        )
        assert stored.entity_ids == ["light.kitchen", "sensor.grid_power"]
        assert stored.selected_count == 2

    with Session(engine) as session:
        persisted = HomeAssistantSelectionService(session).get()
        assert persisted.mode == HomeAssistantSelectionMode.SELECTED
        assert persisted.entity_ids == ["light.kitchen", "sensor.grid_power"]


def test_invalid_replacement_leaves_existing_selection_unchanged() -> None:
    engine = selection_engine()
    with Session(engine) as session:
        service = HomeAssistantSelectionService(session)
        service.replace(
            HomeAssistantSelectionWrite(
                mode=HomeAssistantSelectionMode.SELECTED,
                entity_ids=["sensor.grid_power"],
            )
        )

        with pytest.raises(HomeAssistantSelectionError):
            service.replace(
                HomeAssistantSelectionWrite(
                    mode=HomeAssistantSelectionMode.ALL,
                    entity_ids=["not-an-entity-id"],
                )
            )

        assert service.get().mode == HomeAssistantSelectionMode.SELECTED
        assert service.get().entity_ids == ["sensor.grid_power"]


def test_selection_changes_do_not_delete_existing_asset_links() -> None:
    engine = selection_engine()
    with Session(engine) as session:
        asset_type = AssetType(name="Smart Home", code_prefix="SH")
        session.add(asset_type)
        session.commit()
        session.refresh(asset_type)
        asset = Asset(name="Meter", jarvis_code="SH-001", asset_type_id=asset_type.id)
        session.add(asset)
        session.commit()
        session.refresh(asset)
        HomeAssistantLinkService(session).upsert(
            object_type=HomeAssistantObjectType.ENTITY,
            external_id="sensor.grid_power",
            asset_id=asset.id,
        )

        HomeAssistantSelectionService(session).replace(
            HomeAssistantSelectionWrite(
                mode=HomeAssistantSelectionMode.SELECTED,
                entity_ids=[],
            )
        )

        links = HomeAssistantLinkService(session).list_links()
        assert [item.external_id for item in links.items] == ["sensor.grid_power"]


@pytest.mark.parametrize(
    ("record", "expected_constraint"),
    [
        (
            HomeAssistantSelectionSetting(id=2, mode="all"),
            "ck_home_assistant_selection_settings_singleton",
        ),
        (
            HomeAssistantSelectionSetting(id=1, mode="invalid"),
            "ck_home_assistant_selection_settings_mode",
        ),
    ],
)
def test_selection_setting_database_constraints(record, expected_constraint: str) -> None:
    engine = selection_engine()
    with Session(engine) as session:
        session.add(record)
        with pytest.raises(IntegrityError, match=expected_constraint):
            session.commit()


def test_selection_entity_database_constraints_reject_blank_and_duplicate_ids() -> None:
    engine = selection_engine()
    with Session(engine) as session:
        session.add(HomeAssistantSelectionSetting(id=1, mode="selected"))
        session.commit()
        session.add(HomeAssistantEntitySelection(entity_id=" "))
        with pytest.raises(
            IntegrityError,
            match="ck_home_assistant_entity_selections_entity_id",
        ):
            session.commit()
        session.rollback()

        entity_id = "sensor.grid_power"
        session.add(HomeAssistantEntitySelection(id=uuid4(), entity_id=entity_id))
        session.commit()
        session.add(HomeAssistantEntitySelection(id=uuid4(), entity_id=entity_id))
        with pytest.raises(
            IntegrityError,
            match="UNIQUE constraint failed: home_assistant_entity_selections.entity_id",
        ):
            session.commit()
