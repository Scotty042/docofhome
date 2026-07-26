from datetime import UTC, datetime

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.models.asset_engine import Asset, AssetType
from app.schemas.home_assistant import HomeAssistantObjectType
from app.services.home_assistant_links import (
    HomeAssistantLinkAssetError,
    HomeAssistantLinkNotFoundError,
    HomeAssistantLinkService,
)


def test_home_assistant_links_create_reassign_list_and_delete() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        asset_type = AssetType(name="Smart Home", code_prefix="SH")
        session.add(asset_type)
        session.commit()
        session.refresh(asset_type)
        first = Asset(
            name="Shelly Hauptzähler",
            jarvis_code="SH-001",
            asset_type_id=asset_type.id,
        )
        second = Asset(
            name="Shelly Ersatz",
            jarvis_code="SH-002",
            asset_type_id=asset_type.id,
        )
        session.add(first)
        session.add(second)
        session.commit()
        session.refresh(first)
        session.refresh(second)

        service = HomeAssistantLinkService(session)
        created = service.upsert(
            object_type=HomeAssistantObjectType.DEVICE,
            external_id="device-1",
            asset_id=first.id,
        )
        reassigned = service.upsert(
            object_type=HomeAssistantObjectType.DEVICE,
            external_id="device-1",
            asset_id=second.id,
        )
        entity_link = service.upsert(
            object_type=HomeAssistantObjectType.ENTITY,
            external_id="sensor.grid_power",
            asset_id=second.id,
        )
        links = service.list_links()

        assert created.asset_code == "SH-001"
        assert reassigned.id == created.id
        assert reassigned.asset_code == "SH-002"
        assert entity_link.asset_id == second.id
        assert len(links.items) == 2
        assert {item.object_type for item in links.items} == {
            HomeAssistantObjectType.DEVICE,
            HomeAssistantObjectType.ENTITY,
        }

        second_links = service.list_links(asset_id=second.id)
        assert {item.external_id for item in second_links.items} == {
            "device-1",
            "sensor.grid_power",
        }
        assert service.list_links(asset_id=first.id).items == []

        service.delete(
            object_type=HomeAssistantObjectType.DEVICE,
            external_id="device-1",
        )
        remaining = service.list_links()
        assert [item.external_id for item in remaining.items] == ["sensor.grid_power"]
        with pytest.raises(HomeAssistantLinkNotFoundError):
            service.delete(
                object_type=HomeAssistantObjectType.DEVICE,
                external_id="device-1",
            )


def test_home_assistant_link_rejects_missing_and_archived_assets() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        asset_type = AssetType(name="Smart Home", code_prefix="SH")
        session.add(asset_type)
        session.commit()
        session.refresh(asset_type)
        archived = Asset(
            name="Archiviertes Gerät",
            jarvis_code="SH-001",
            asset_type_id=asset_type.id,
            deleted_at=datetime.now(UTC),
        )
        session.add(archived)
        session.commit()
        session.refresh(archived)
        service = HomeAssistantLinkService(session)

        with pytest.raises(HomeAssistantLinkAssetError):
            service.upsert(
                object_type=HomeAssistantObjectType.DEVICE,
                external_id="device-1",
                asset_id=archived.id,
            )


def test_home_assistant_bulk_bindings_support_roles_and_reject_implicit_transfer() -> None:
    from app.schemas.home_assistant import (
        HomeAssistantAssetBindingsWrite,
        HomeAssistantEntityBindingWrite,
        HomeAssistantEntityRole,
    )
    from app.services.home_assistant_links import HomeAssistantLinkConflictError

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        asset_type = AssetType(name="Smart Home", code_prefix="SH")
        session.add(asset_type)
        session.commit()
        session.refresh(asset_type)
        first = Asset(name="Zähler", jarvis_code="SH-001", asset_type_id=asset_type.id)
        second = Asset(name="Ersatz", jarvis_code="SH-002", asset_type_id=asset_type.id)
        session.add(first)
        session.add(second)
        session.commit()
        session.refresh(first)
        session.refresh(second)

        service = HomeAssistantLinkService(session)
        saved = service.replace_asset_bindings(
            first.id,
            HomeAssistantAssetBindingsWrite(
                device_ids=["device-meter"],
                entities=[
                    HomeAssistantEntityBindingWrite(
                        external_id="sensor.grid_power",
                        role=HomeAssistantEntityRole.PRIMARY_LIVE,
                    ),
                    HomeAssistantEntityBindingWrite(
                        external_id="sensor.grid_voltage",
                        role=HomeAssistantEntityRole.VOLTAGE,
                    ),
                ],
            ),
        )

        assert {item.external_id for item in saved.items} == {
            "device-meter",
            "sensor.grid_power",
            "sensor.grid_voltage",
        }
        roles = {item.external_id: item.role for item in saved.items}
        assert roles["sensor.grid_power"] == HomeAssistantEntityRole.PRIMARY_LIVE
        assert roles["sensor.grid_voltage"] == HomeAssistantEntityRole.VOLTAGE

        with pytest.raises(HomeAssistantLinkConflictError):
            service.replace_asset_bindings(
                second.id,
                HomeAssistantAssetBindingsWrite(
                    entities=[
                        HomeAssistantEntityBindingWrite(
                            external_id="sensor.grid_power",
                            role=HomeAssistantEntityRole.PRIMARY_LIVE,
                        )
                    ]
                ),
            )
