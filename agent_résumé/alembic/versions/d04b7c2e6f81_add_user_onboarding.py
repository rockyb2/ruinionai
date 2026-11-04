"""Ajoute la progression du tutoriel utilisateur.

Revision ID: d04b7c2e6f81
Revises: c93f4a1d2e70
"""

from alembic import op
import sqlalchemy as sa


revision = "d04b7c2e6f81"
down_revision = "c93f4a1d2e70"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("onboarding_version", sa.Integer(), server_default="1", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("onboarding_steps", sa.JSON(), server_default="{}", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("onboarding_completed_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("onboarding_dismissed_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "onboarding_dismissed_at")
    op.drop_column("users", "onboarding_completed_at")
    op.drop_column("users", "onboarding_steps")
    op.drop_column("users", "onboarding_version")
