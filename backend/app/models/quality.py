from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint
from sqlmodel import Field, SQLModel


class QualityRun(SQLModel, table=True):
    __tablename__ = "quality_runs"
    __table_args__ = (
        CheckConstraint(
            "trigger IN ('manual', 'scheduled')",
            name="ck_quality_runs_trigger",
        ),
        CheckConstraint("score >= 0 AND score <= 100", name="ck_quality_runs_score"),
        CheckConstraint(
            "issue_count >= 0 AND error_count >= 0 AND warning_count >= 0 AND info_count >= 0",
            name="ck_quality_runs_counts",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    trigger: str = Field(index=True, max_length=20)
    score: int = Field(default=100, ge=0, le=100)
    issue_count: int = Field(default=0, ge=0)
    error_count: int = Field(default=0, ge=0)
    warning_count: int = Field(default=0, ge=0)
    info_count: int = Field(default=0, ge=0)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    completed_at: datetime | None = Field(default=None, index=True)


class QualityIssue(SQLModel, table=True):
    __tablename__ = "quality_issues"
    __table_args__ = (
        CheckConstraint(
            "severity IN ('error', 'warning', 'info')",
            name="ck_quality_issues_severity",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    run_id: UUID = Field(foreign_key="quality_runs.id", index=True)
    category: str = Field(index=True, max_length=50)
    severity: str = Field(index=True, max_length=20)
    code: str = Field(index=True, max_length=100)
    title: str = Field(max_length=250)
    description: str = Field(max_length=2000)
    target_type: str | None = Field(default=None, max_length=50)
    target_id: UUID | None = Field(default=None, index=True)
    route: str | None = Field(default=None, max_length=1000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
