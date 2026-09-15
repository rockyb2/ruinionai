"""add meeting report path

Revision ID: 9a8b7c6d5e4f
Revises: 1d6cb7a4a9b8
Create Date: 2026-09-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9a8b7c6d5e4f"
down_revision: Union[str, Sequence[str], None] = "1d6cb7a4a9b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("meetings", sa.Column("report_path", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("meetings", "report_path")
