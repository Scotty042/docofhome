from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine

from app.models.asset_engine import Asset, AssetType
from app.models.immich import ImmichAssetLink


def test_immich_link_database_constraints_reject_duplicates_and_invalid_dimensions() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        asset_type = AssetType(name="Panel", code_prefix="PNL")
        session.add(asset_type)
        session.commit()
        asset = Asset(name="Main", jarvis_code="PNL-001", asset_type_id=asset_type.id)
        session.add(asset)
        session.commit()
        session.refresh(asset)
        external_id = str(uuid4())
        session.add(
            ImmichAssetLink(
                asset_id=asset.id,
                immich_asset_id=external_id,
                original_file_name="main.jpg",
            )
        )
        session.commit()

        session.add(
            ImmichAssetLink(
                asset_id=asset.id,
                immich_asset_id=external_id,
                original_file_name="duplicate.jpg",
            )
        )
        with pytest.raises(IntegrityError, match="UNIQUE constraint failed"):
            session.commit()
        session.rollback()

        session.add(
            ImmichAssetLink(
                asset_id=asset.id,
                immich_asset_id=str(uuid4()),
                original_file_name="invalid.jpg",
                width=0,
            )
        )
        with pytest.raises(IntegrityError, match="ck_immich_asset_links_width"):
            session.commit()
