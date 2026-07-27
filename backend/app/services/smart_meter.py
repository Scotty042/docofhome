from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, delete, select

from app.models.asset_engine import Asset, AssetType
from app.models.electrical_topology import ElectricalConnection
from app.models.smart_meter import (
    SmartMeterMeasurementEntity,
    SmartMeterMeasurementPoint,
)
from app.repositories.electrical_topology import (
    ElectricalConnectionRepository,
    ElectricalEndpointRepository,
)
from app.schemas.electrical_topology import ElectricalEndpointKind
from app.schemas.smart_meter import (
    SmartMeterMeasurementEntityRead,
    SmartMeterMeasurementPointRead,
    SmartMeterMeasurementPointWrite,
)
from app.services.electrical import (
    ElectricalConflictError,
    ElectricalNotFoundError,
    ElectricalValidationError,
)


class SmartMeterMeasurementService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.connections = ElectricalConnectionRepository(session)
        self.endpoints = ElectricalEndpointRepository(session)

    def list_for_asset(self, asset_id: UUID) -> list[SmartMeterMeasurementPointRead]:
        self._smart_meter_asset(asset_id)
        records = self.session.exec(
            select(SmartMeterMeasurementPoint)
            .where(
                SmartMeterMeasurementPoint.smart_meter_asset_id == asset_id,
                col(SmartMeterMeasurementPoint.deleted_at).is_(None),
            )
            .order_by(
                col(SmartMeterMeasurementPoint.channel_name),
                col(SmartMeterMeasurementPoint.name),
            )
        ).all()
        return [self._read(record) for record in records]

    def list_all_active(self) -> list[SmartMeterMeasurementPointRead]:
        records = self.session.exec(
            select(SmartMeterMeasurementPoint)
            .where(col(SmartMeterMeasurementPoint.deleted_at).is_(None))
            .order_by(
                col(SmartMeterMeasurementPoint.smart_meter_asset_id),
                col(SmartMeterMeasurementPoint.channel_name),
            )
        ).all()
        result: list[SmartMeterMeasurementPointRead] = []
        for record in records:
            try:
                result.append(self._read(record))
            except ElectricalNotFoundError:
                continue
        return result

    def create(
        self,
        asset_id: UUID,
        payload: SmartMeterMeasurementPointWrite,
    ) -> SmartMeterMeasurementPointRead:
        self._smart_meter_asset(asset_id)
        self._validate_connection(payload.connection_id)
        self._validate_channel(asset_id, payload.channel_name)
        record = SmartMeterMeasurementPoint(
            smart_meter_asset_id=asset_id,
            **payload.model_dump(mode="python", exclude={"entities"}),
        )
        self.session.add(record)
        self._flush()
        self._replace_entities(record.id, payload)
        self._commit()
        return self._read(record)

    def update(
        self,
        asset_id: UUID,
        point_id: UUID,
        payload: SmartMeterMeasurementPointWrite,
    ) -> SmartMeterMeasurementPointRead:
        self._smart_meter_asset(asset_id)
        record = self._point(asset_id, point_id)
        self._validate_connection(payload.connection_id)
        self._validate_channel(asset_id, payload.channel_name, exclude_id=point_id)
        record.sqlmodel_update(payload.model_dump(mode="python", exclude={"entities"}))
        record.updated_at = datetime.now(UTC)
        self._replace_entities(record.id, payload)
        self._commit()
        return self._read(record)

    def delete(self, asset_id: UUID, point_id: UUID) -> None:
        record = self._point(asset_id, point_id)
        now = datetime.now(UTC)
        record.deleted_at = now
        record.updated_at = now
        self.session.exec(
            delete(SmartMeterMeasurementEntity).where(
                SmartMeterMeasurementEntity.measurement_point_id == point_id
            )
        )
        self._commit()

    def active_for_connection(self, connection_id: UUID) -> list[SmartMeterMeasurementPoint]:
        return list(
            self.session.exec(
                select(SmartMeterMeasurementPoint).where(
                    SmartMeterMeasurementPoint.connection_id == connection_id,
                    col(SmartMeterMeasurementPoint.deleted_at).is_(None),
                )
            ).all()
        )

    def active_for_asset(self, asset_id: UUID) -> list[SmartMeterMeasurementPoint]:
        return list(
            self.session.exec(
                select(SmartMeterMeasurementPoint).where(
                    SmartMeterMeasurementPoint.smart_meter_asset_id == asset_id,
                    col(SmartMeterMeasurementPoint.deleted_at).is_(None),
                )
            ).all()
        )

    def _smart_meter_asset(self, asset_id: UUID) -> Asset:
        asset = self.session.get(Asset, asset_id)
        if asset is None or asset.deleted_at is not None:
            raise ElectricalNotFoundError
        asset_type = self.session.get(AssetType, asset.asset_type_id)
        normalized = asset_type.name.strip().casefold() if asset_type else ""
        if "smart meter" not in normalized and "smartmeter" not in normalized:
            raise ElectricalValidationError(
                "Messklemmen können nur an einem Asset-Typ Smart Meter gepflegt werden"
            )
        return asset

    def _point(self, asset_id: UUID, point_id: UUID) -> SmartMeterMeasurementPoint:
        record = self.session.get(SmartMeterMeasurementPoint, point_id)
        if (
            record is None
            or record.deleted_at is not None
            or record.smart_meter_asset_id != asset_id
        ):
            raise ElectricalNotFoundError
        return record

    def _validate_connection(self, connection_id: UUID) -> ElectricalConnection:
        record = self.connections.get(connection_id)
        if record is None:
            raise ElectricalValidationError(
                "Die ausgewählte Verkabelung existiert nicht oder ist archiviert"
            )
        return record

    def _validate_channel(
        self,
        asset_id: UUID,
        channel_name: str,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        normalized = channel_name.strip().casefold()
        records = self.session.exec(
            select(SmartMeterMeasurementPoint).where(
                SmartMeterMeasurementPoint.smart_meter_asset_id == asset_id,
                col(SmartMeterMeasurementPoint.deleted_at).is_(None),
            )
        ).all()
        if any(
            item.id != exclude_id and item.channel_name.strip().casefold() == normalized
            for item in records
        ):
            raise ElectricalConflictError(
                "Dieser Messkanal ist am Smart Meter bereits vorhanden"
            )

    def _replace_entities(
        self,
        point_id: UUID,
        payload: SmartMeterMeasurementPointWrite,
    ) -> None:
        self.session.exec(
            delete(SmartMeterMeasurementEntity).where(
                SmartMeterMeasurementEntity.measurement_point_id == point_id
            )
        )
        now = datetime.now(UTC)
        for item in payload.entities:
            self.session.add(
                SmartMeterMeasurementEntity(
                    measurement_point_id=point_id,
                    entity_id=item.entity_id,
                    role=item.role.value,
                    created_at=now,
                    updated_at=now,
                )
            )
        self._flush()

    def _read(self, record: SmartMeterMeasurementPoint) -> SmartMeterMeasurementPointRead:
        asset = self.session.get(Asset, record.smart_meter_asset_id)
        connection = self.connections.get(record.connection_id)
        if asset is None or connection is None:
            raise ElectricalNotFoundError
        source = self.endpoints.resolve(
            ElectricalEndpointKind(connection.source_kind),
            connection.source_id,
        )
        target = self.endpoints.resolve(
            ElectricalEndpointKind(connection.target_kind),
            connection.target_id,
        )
        if source is None or target is None:
            raise ElectricalNotFoundError
        entities = self.session.exec(
            select(SmartMeterMeasurementEntity)
            .where(SmartMeterMeasurementEntity.measurement_point_id == record.id)
            .order_by(
                col(SmartMeterMeasurementEntity.role),
                col(SmartMeterMeasurementEntity.entity_id),
            )
        ).all()
        return SmartMeterMeasurementPointRead.model_validate(
            {
                **record.model_dump(),
                "smart_meter_asset_name": asset.name,
                "smart_meter_asset_code": asset.jarvis_code,
                "connection_source_name": source.name,
                "connection_target_name": target.name,
                "connection_label": connection.label,
                "entities": [
                    SmartMeterMeasurementEntityRead.model_validate(item)
                    for item in entities
                ],
            }
        )

    def _flush(self) -> None:
        try:
            self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise ElectricalConflictError(
                "Der Smart-Meter-Messpunkt konnte wegen eines Datenkonflikts "
                "nicht gespeichert werden"
            ) from exc
        except Exception:
            self.session.rollback()
            raise

    def _commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ElectricalConflictError(
                "Der Smart-Meter-Messpunkt konnte wegen eines Datenkonflikts "
                "nicht gespeichert werden"
            ) from exc
        except Exception:
            self.session.rollback()
            raise
