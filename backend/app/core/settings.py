from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _read_version() -> str:
    """Read the single release version in source and container layouts."""

    module_path = Path(__file__).resolve()
    candidates = (
        module_path.parents[3] / "VERSION",
        module_path.parents[2] / "VERSION",
    )
    for candidate in candidates:
        if candidate.is_file():
            version = candidate.read_text(encoding="utf-8").strip()
            if version:
                return version
    raise RuntimeError("The required VERSION file is missing or empty")


class Settings(BaseSettings):
    """Bootstrap settings required before the web configuration is available.

    User-facing settings belong in the persistent database. Environment variables
    use the ``JARVIS_`` prefix, for example ``JARVIS_LOG_LEVEL=DEBUG``.
    """

    app_name: str = "DocOfHome"
    app_version: str = _read_version()
    data_dir: Path = Path("/data")
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_prefix="JARVIS_",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized = value.upper()
        allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
        if normalized not in allowed:
            raise ValueError(f"Unsupported log level: {value}")
        return normalized

    @property
    def database_path(self) -> Path:
        return self.data_dir / "database" / "jarvis.sqlite3"

    @property
    def static_dir(self) -> Path:
        return Path(__file__).resolve().parents[2] / "static"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
