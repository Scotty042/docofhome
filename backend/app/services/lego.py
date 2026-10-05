from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy import select as sa_select
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.models.asset_engine import Location
from app.models.lego import LegoSet
from app.schemas.lego import LegoDashboard, LegoSetRead, LegoSetWrite


class LegoConflictError(ValueError):
    pass


class LegoService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def read(self, row: LegoSet) -> LegoSetRead:
        location = self.session.get(Location, row.location_id) if row.location_id else None
        return LegoSetRead.model_validate(
            {**row.model_dump(), "location_name": location.name if location else None}
        )

    def get(self, set_id: UUID) -> LegoSet:
        row = self.session.get(LegoSet, set_id)
        if row is None:
            raise LookupError("LEGO-Set nicht gefunden")
        return row

    def search(
        self, query: str = "", set_number: str | None = None, offset: int = 0, limit: int = 100
    ) -> dict[str, Any]:
        statement = select(LegoSet)
        if query.strip():
            needle = f"%{query.strip()}%"
            statement = statement.outerjoin(Location, col(LegoSet.location_id) == col(Location.id))
            statement = statement.where(
                or_(
                    col(LegoSet.name).ilike(needle),
                    col(LegoSet.set_number).ilike(needle),
                    col(LegoSet.theme).ilike(needle),
                    col(LegoSet.storage_note).ilike(needle),
                    col(Location.name).ilike(needle),
                )
            )
        if set_number:
            statement = statement.where(
                LegoSet.set_number == LegoSetWrite.normalize_number(set_number)
            )
        total = self.session.exec(select(func.count()).select_from(statement.subquery())).one()
        items = [
            self.read(row).model_dump(mode="json")
            for row in self.session.exec(
                statement.order_by(col(LegoSet.name), col(LegoSet.id)).offset(offset).limit(limit)
            )
        ]
        more = offset + len(items) < total
        return {
            "items": items,
            "total": total,
            "count": len(items),
            "has_more": more,
            "next_offset": offset + len(items) if more else None,
        }

    def save(self, data: LegoSetWrite, set_id: UUID | None = None) -> LegoSetRead:
        if data.location_id:
            location = self.session.get(Location, data.location_id)
            if location is None or location.deleted_at is not None:
                raise ValueError("Lagerort nicht gefunden oder archiviert")
        existing = self.session.exec(
            select(LegoSet).where(LegoSet.set_number == data.set_number)
        ).first()
        if existing and existing.id != set_id:
            raise LegoConflictError(f"Set {data.set_number} ist bereits vorhanden")
        row = self.get(set_id) if set_id else LegoSet(set_number=data.set_number, name=data.name)
        for key, value in data.model_dump().items():
            setattr(row, key, value)
        row.updated_at = datetime.now(UTC)
        self.session.add(row)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise LegoConflictError(
                "Setnummer bereits vorhanden oder Lagerort nicht mehr verfügbar"
            ) from exc
        self.session.refresh(row)
        return self.read(row)

    def dashboard(self) -> LegoDashboard:
        total, price, known_prices, parts, known_parts = self.session.execute(
            sa_select(
                func.count(col(LegoSet.id)),
                func.sum(col(LegoSet.purchase_price)),
                func.count(col(LegoSet.purchase_price)),
                func.sum(col(LegoSet.parts_count)),
                func.count(col(LegoSet.parts_count)),
            )
        ).one()
        return LegoDashboard(
            sets_count=total,
            purchase_total=price or Decimal("0.00"),
            missing_prices=total - known_prices,
            parts_total=parts or 0,
            missing_parts=total - known_parts,
        )

    def delete(self, set_id: UUID) -> None:
        self.session.delete(self.get(set_id))
        self.session.commit()
