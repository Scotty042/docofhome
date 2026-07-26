from sqlmodel import Session, select

from app.models.application_setting import ApplicationSetting
from app.models.integration_setting import IntegrationSetting


class SettingsRepository:
    """Database operations for application and integration settings."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_application(self) -> ApplicationSetting | None:
        return self.session.get(ApplicationSetting, 1)

    def add_application(self, setting: ApplicationSetting) -> None:
        self.session.add(setting)

    def list_integrations(self) -> list[IntegrationSetting]:
        statement = select(IntegrationSetting).order_by(IntegrationSetting.kind)
        return list(self.session.exec(statement).all())

    def get_integration(self, kind: str) -> IntegrationSetting | None:
        statement = select(IntegrationSetting).where(IntegrationSetting.kind == kind)
        return self.session.exec(statement).one_or_none()

    def add_integration(self, setting: IntegrationSetting) -> None:
        self.session.add(setting)
