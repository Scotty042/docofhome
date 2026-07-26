from uuid import UUID

from sqlmodel import Session, col, select

from app.models.energy import EnergyComponent, EnergyConfiguration


class EnergyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def configuration(self) -> EnergyConfiguration | None:
        return self.session.get(EnergyConfiguration, 1)

    def list_components(self, *, include_archived: bool = False) -> list[EnergyComponent]:
        statement = select(EnergyComponent)
        if not include_archived:
            statement = statement.where(col(EnergyComponent.deleted_at).is_(None))
        statement = statement.order_by(
            col(EnergyComponent.deleted_at).is_not(None),
            col(EnergyComponent.sort_order),
            col(EnergyComponent.component_type),
            col(EnergyComponent.name),
        )
        return list(self.session.exec(statement).all())

    def component(
        self, component_id: UUID, *, include_archived: bool = False
    ) -> EnergyComponent | None:
        record = self.session.get(EnergyComponent, component_id)
        if record is None or (record.deleted_at is not None and not include_archived):
            return None
        return record
