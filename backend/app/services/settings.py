import json
from datetime import UTC, datetime
from uuid import UUID

from sqlmodel import Session

from app.models.application_setting import ApplicationSetting
from app.models.integration_setting import IntegrationSetting
from app.repositories.settings import SettingsRepository
from app.schemas.settings import (
    ConfigurationRead,
    ConfigurationWrite,
    IntegrationKind,
    IntegrationRead,
    Language,
    ModuleKey,
    SetupStatusRead,
    ThemePreference,
)
from app.services.asset_engine import LocationService


class SetupAlreadyCompletedError(RuntimeError):
    """Raised when first-run setup is submitted more than once."""


class SetupNotCompletedError(RuntimeError):
    """Raised when settings are requested before first-run setup."""


class InvalidIntegrationError(ValueError):
    """Raised when an enabled integration lacks required credentials."""


class SettingsService:
    """Coordinate validated settings changes in a single transaction."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = SettingsRepository(session)

    def get_setup_status(self) -> SetupStatusRead:
        setting = self.repository.get_application()
        completed = setting is not None and setting.setup_completed_at is not None
        return SetupStatusRead(setup_required=not completed, completed=completed)

    def get_configuration(self) -> ConfigurationRead:
        setting = self.repository.get_application()
        if setting is None or setting.setup_completed_at is None:
            raise SetupNotCompletedError
        return self._to_read_model(setting)

    def complete_setup(self, payload: ConfigurationWrite) -> ConfigurationRead:
        existing = self.repository.get_application()
        if existing is not None and existing.setup_completed_at is not None:
            raise SetupAlreadyCompletedError

        now = datetime.now(UTC)
        setting = existing or ApplicationSetting(
            installation_name=payload.installation_name,
            language=payload.language.value,
            timezone=payload.timezone,
            theme=payload.theme.value,
            enabled_modules_json=self._serialize_modules(payload.enabled_modules),
        )
        if existing is None:
            self.repository.add_application(setting)

        try:
            self._apply_configuration(setting, payload, now)
            LocationService(self.session).ensure_root(
                payload.installation_name,
                rename_existing=True,
            )
            setting.setup_completed_at = now
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return self._to_read_model(setting)

    def update_configuration(self, payload: ConfigurationWrite) -> ConfigurationRead:
        setting = self.repository.get_application()
        if setting is None or setting.setup_completed_at is None:
            raise SetupNotCompletedError

        try:
            self._apply_configuration(setting, payload, datetime.now(UTC))
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return self._to_read_model(setting)

    def _apply_configuration(
        self,
        setting: ApplicationSetting,
        payload: ConfigurationWrite,
        now: datetime,
    ) -> None:
        setting.installation_name = payload.installation_name
        setting.language = payload.language.value
        setting.timezone = payload.timezone
        setting.theme = payload.theme.value
        setting.online_product_image_search_enabled = (
            payload.online_product_image_search_enabled
        )
        setting.product_image_source_wikimedia_enabled = (
            payload.product_image_source_wikimedia_enabled
        )
        setting.product_image_source_duckduckgo_enabled = (
            payload.product_image_source_duckduckgo_enabled
        )
        setting.enabled_modules_json = self._serialize_modules(payload.enabled_modules)
        setting.updated_at = now

        submitted = {integration.kind: integration for integration in payload.integrations}
        for kind in IntegrationKind:
            data = submitted.get(kind)
            stored = self.repository.get_integration(kind.value)
            enabled = data.enabled if data is not None else False
            base_url = data.base_url if data is not None else None
            account = data.account if data is not None else None
            selected_album_id = data.selected_album_id if data is not None else None
            document_root = data.document_root if data is not None else None
            new_secret = data.secret.get_secret_value() if data and data.secret else None
            existing_secret = stored.secret if stored is not None else None

            if enabled and (base_url is None or (new_secret is None and existing_secret is None)):
                raise InvalidIntegrationError(
                    f"Enabled integration '{kind.value}' requires a URL and secret"
                )
            if enabled and kind == IntegrationKind.NEXTCLOUD and account is None:
                raise InvalidIntegrationError(
                    "Enabled Nextcloud integration requires an account or username"
                )
            if enabled and kind == IntegrationKind.FRITZBOX and account is None:
                raise InvalidIntegrationError(
                    "Enabled FRITZ!Box integration requires an account or username"
                )

            if stored is None:
                stored = IntegrationSetting(kind=kind.value)
                self.repository.add_integration(stored)
            stored.enabled = enabled
            stored.base_url = base_url
            stored.account = account
            stored.selected_album_id = (
                str(selected_album_id)
                if kind == IntegrationKind.IMMICH and selected_album_id is not None
                else None
            )
            stored.document_root = (
                (document_root or "docofhome/Documents")
                if kind == IntegrationKind.NEXTCLOUD
                else None
            )
            if new_secret is not None:
                stored.secret = new_secret
            stored.updated_at = now

    def _to_read_model(self, setting: ApplicationSetting) -> ConfigurationRead:
        if setting.setup_completed_at is None:
            raise SetupNotCompletedError

        stored = {item.kind: item for item in self.repository.list_integrations()}
        integrations = []
        for kind in IntegrationKind:
            integration = stored.get(kind.value)
            document_root = None
            if kind == IntegrationKind.NEXTCLOUD:
                document_root = (
                    integration.document_root if integration and integration.document_root else None
                ) or "docofhome/Documents"
            integrations.append(
                IntegrationRead(
                    kind=kind,
                    enabled=integration.enabled if integration else False,
                    base_url=integration.base_url if integration else None,
                    account=integration.account if integration else None,
                    secret_configured=bool(integration and integration.secret),
                    selected_album_id=(
                        UUID(integration.selected_album_id)
                        if integration and integration.selected_album_id
                        else None
                    ),
                    document_root=document_root,
                )
            )
        return ConfigurationRead(
            installation_name=setting.installation_name,
            language=Language(setting.language),
            timezone=setting.timezone,
            theme=ThemePreference(setting.theme),
            online_product_image_search_enabled=(
                setting.online_product_image_search_enabled
            ),
            product_image_source_wikimedia_enabled=(
                setting.product_image_source_wikimedia_enabled
            ),
            product_image_source_duckduckgo_enabled=(
                setting.product_image_source_duckduckgo_enabled
            ),
            enabled_modules=self._deserialize_modules(setting.enabled_modules_json),
            setup_completed_at=setting.setup_completed_at,
            integrations=integrations,
        )

    @staticmethod
    def _serialize_modules(modules: list[ModuleKey]) -> str:
        return json.dumps([module.value for module in modules], separators=(",", ":"))

    @staticmethod
    def _deserialize_modules(raw: str) -> list[ModuleKey]:
        try:
            values = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return list(ModuleKey)
        if not isinstance(values, list):
            return list(ModuleKey)
        modules: list[ModuleKey] = []
        for value in values:
            try:
                module = ModuleKey(value)
            except (TypeError, ValueError):
                continue
            if module not in modules:
                modules.append(module)
        return modules
