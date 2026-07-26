"""Create persistent documentation quality reports and issues.

Revision ID: 0021
Revises: 0020
Create Date: 2026-07-22
"""

import json
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _update_module(module: str, *, add: bool) -> None:
    connection = op.get_bind()
    rows = connection.execute(
        sa.text("SELECT id, enabled_modules_json FROM application_settings")
    ).mappings()
    for row in rows:
        try:
            modules = json.loads(row["enabled_modules_json"])
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(modules, list):
            continue
        modules = [value for value in modules if isinstance(value, str) and value != module]
        if add:
            modules.append(module)
        connection.execute(
            sa.text(
                "UPDATE application_settings SET enabled_modules_json = :modules WHERE id = :id"
            ),
            {"modules": json.dumps(modules, separators=(",", ":")), "id": row["id"]},
        )


def upgrade() -> None:
    op.create_table(
        "quality_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("trigger", sa.String(length=20), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("issue_count", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("warning_count", sa.Integer(), nullable=False),
        sa.Column("info_count", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("trigger IN ('manual', 'scheduled')", name="ck_quality_runs_trigger"),
        sa.CheckConstraint("score >= 0 AND score <= 100", name="ck_quality_runs_score"),
        sa.CheckConstraint(
            "issue_count >= 0 AND error_count >= 0 AND warning_count >= 0 AND info_count >= 0",
            name="ck_quality_runs_counts",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quality_runs_trigger", "quality_runs", ["trigger"])
    op.create_index("ix_quality_runs_started_at", "quality_runs", ["started_at"])
    op.create_index("ix_quality_runs_completed_at", "quality_runs", ["completed_at"])

    op.create_table(
        "quality_issues",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=250), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=True),
        sa.Column("target_id", sa.Uuid(), nullable=True),
        sa.Column("route", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "severity IN ('error', 'warning', 'info')",
            name="ck_quality_issues_severity",
        ),
        sa.ForeignKeyConstraint(["run_id"], ["quality_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("run_id", "category", "severity", "code", "target_id"):
        op.create_index(f"ix_quality_issues_{column}", "quality_issues", [column])
    _update_module("quality", add=True)


def downgrade() -> None:
    _update_module("quality", add=False)
    for column in reversed(("run_id", "category", "severity", "code", "target_id")):
        op.drop_index(f"ix_quality_issues_{column}", table_name="quality_issues")
    op.drop_table("quality_issues")
    op.drop_index("ix_quality_runs_completed_at", table_name="quality_runs")
    op.drop_index("ix_quality_runs_started_at", table_name="quality_runs")
    op.drop_index("ix_quality_runs_trigger", table_name="quality_runs")
    op.drop_table("quality_runs")
