from datetime import UTC, datetime

from sqlmodel import Field, SQLModel

DEFAULT_ENABLED_MODULES_JSON = (
    '["locations","electrical","assets","master_data","network",'
    '"smart_home","consumption","wiki","maintenance","quality"]'
)
DEFAULT_MAIN_MENU_MODULES_JSON = DEFAULT_ENABLED_MODULES_JSON


class ApplicationSetting(SQLModel, table=True):
    """Singleton containing the user-facing DocOfHome configuration."""

    __tablename__ = "application_settings"

    id: int = Field(default=1, primary_key=True)
    installation_name: str = Field(max_length=100)
    language: str = Field(default="de", max_length=10)
    timezone: str = Field(max_length=100)
    theme: str = Field(default="dark", max_length=20)
    enabled_modules_json: str = Field(default=DEFAULT_ENABLED_MODULES_JSON)
    main_menu_modules_json: str = Field(default=DEFAULT_MAIN_MENU_MODULES_JSON)
    online_product_image_search_enabled: bool = False
    product_image_source_wikimedia_enabled: bool = True
    product_image_source_duckduckgo_enabled: bool = True
    setup_completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
