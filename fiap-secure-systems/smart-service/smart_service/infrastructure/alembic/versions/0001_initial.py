"""initial smart_db schema

Revision ID: 0001
Revises:
Create Date: 2026-05-07
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "job_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
            unique=True,
        ),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("asset_keys", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("prompt_version", sa.String(length=16), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("result", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("finished_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index("analysis_runs_by_session", "analysis_runs", ["session_id"])

    op.create_table(
        "processed_jobs",
        sa.Column("job_id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("processed_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("processed_jobs")
    op.drop_index("analysis_runs_by_session", table_name="analysis_runs")
    op.drop_table("analysis_runs")
