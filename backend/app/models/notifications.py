from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint
from sqlmodel import Field, SQLModel


class PushDelivery(SQLModel, table=True):
    __tablename__ = "push_deliveries"
    __table_args__ = (
        CheckConstraint("provider IN ('pushover','ntfy')", name="ck_push_provider"),
        CheckConstraint("status IN ('pending','sending','sent','failed')", name="ck_push_status"),
    )
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    delivery_key: str = Field(max_length=200, unique=True, index=True)
    provider: str = Field(max_length=20)
    kind: str = Field(default="daily", max_length=20)
    status: str = Field(default="pending", max_length=20)
    attempts: int = 0
    detail: str | None = Field(default=None, max_length=300)
    last_attempt_at: datetime | None = None
    next_retry_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
