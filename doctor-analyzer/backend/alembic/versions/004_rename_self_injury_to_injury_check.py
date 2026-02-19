"""Rename self_injury_check column to injury_check.

Revision ID: 004
Revises: 003
Create Date: 2026-02-18

"""
from typing import Sequence, Union

from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("analysis_sessions", "self_injury_check", new_column_name="injury_check")


def downgrade() -> None:
    op.alter_column("analysis_sessions", "injury_check", new_column_name="self_injury_check")
