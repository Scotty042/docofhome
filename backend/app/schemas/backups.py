from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class BackupCreateRequest(BaseModel):
    upload_to_nextcloud: bool = False
    nextcloud_folder: str = Field(default="DocOfHome/Backups", max_length=500)


class BackupRecord(BaseModel):
    filename: str
    created_at: datetime
    size_bytes: int = Field(ge=0)
    sha256: str
    database_size_bytes: int = Field(ge=0)
    app_version: str
    nextcloud_uploaded: bool = False


class BackupListRead(BaseModel):
    items: list[BackupRecord]


class RemoteBackupRecord(BaseModel):
    filename: str
    size_bytes: int = Field(ge=0)
    modified_at: datetime | None = None
    local_available: bool = False


class RemoteBackupListRead(BaseModel):
    items: list[RemoteBackupRecord]


class BackupValidationRead(BaseModel):
    valid: bool
    message: str
    record: BackupRecord | None = None


class BackupRestoreRequest(BaseModel):
    confirmation: str


class BackupRestoreRead(BaseModel):
    scheduled: bool
    restart_required: bool
    message: str


class BackupScheduleWrite(BaseModel):
    enabled: bool = False
    interval_hours: int = Field(default=24, ge=1, le=8760)
    retention_count: int = Field(default=10, ge=1, le=100)
    upload_to_nextcloud: bool = False
    nextcloud_folder: str = Field(default="DocOfHome/Backups", max_length=500)

    @field_validator("nextcloud_folder")
    @classmethod
    def normalize_folder(cls, value: str) -> str:
        parts = [part for part in value.strip("/").split("/") if part]
        if not parts or any(part in {".", ".."} for part in parts):
            raise ValueError("Invalid Nextcloud folder")
        return "/".join(parts)


class BackupScheduleRead(BackupScheduleWrite):
    last_attempt_at: datetime | None = None
    last_success_at: datetime | None = None
    last_error: str | None = None
