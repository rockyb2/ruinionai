"""Enregistre l'acceptation des conditions d'utilisation.

Revision ID: b82d4c7e1f30
Revises: a71c9e5d2b40
"""

from alembic import op
import sqlalchemy as sa


revision = "b82d4c7e1f30"
down_revision = "a71c9e5d2b40"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("accepted_terms_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("accepted_terms_version", sa.String(length=20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "accepted_terms_version")
    op.drop_column("users", "accepted_terms_at")
