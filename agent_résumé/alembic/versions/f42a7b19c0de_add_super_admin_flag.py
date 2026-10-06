"""add super admin flag

Revision ID: f42a7b19c0de
Revises: e31a62b904fc
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f42a7b19c0de"
down_revision: Union[str, Sequence[str], None] = "e31a62b904fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_super_admin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "is_super_admin")
