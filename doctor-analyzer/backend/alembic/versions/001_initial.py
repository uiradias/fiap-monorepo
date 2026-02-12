"""Initial migration — patients and analysis_sessions tables.

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("codename", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "analysis_sessions",
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("video_s3_key", sa.String(512), nullable=True),
        sa.Column("results_s3_key", sa.String(512), nullable=True),
        sa.Column(
            "emotion_summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "clinical_indicators",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["patient_id"], ["patients.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("session_id"),
    )

    op.create_index("ix_analysis_sessions_patient_id", "analysis_sessions", ["patient_id"])
    op.create_index("ix_analysis_sessions_status", "analysis_sessions", ["status"])
    op.create_index("ix_analysis_sessions_created_at", "analysis_sessions", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_analysis_sessions_created_at", table_name="analysis_sessions")
    op.drop_index("ix_analysis_sessions_status", table_name="analysis_sessions")
    op.drop_index("ix_analysis_sessions_patient_id", table_name="analysis_sessions")
    op.drop_table("analysis_sessions")
    op.drop_table("patients")
