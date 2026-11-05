"""Ajoute les codes temporaires de reinitialisation du mot de passe.

Revision ID: e84a6c1b2d90
Revises: d04b7c2e6f81
"""

from alembic import op
import sqlalchemy as sa


revision = "e84a6c1b2d90"
down_revision = "d04b7c2e6f81"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "password_reset_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("failed_attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_password_reset_codes_user_id",
        "password_reset_codes",
        ["user_id"],
    )
    op.create_index(
        "ix_password_reset_codes_code_hash",
        "password_reset_codes",
        ["code_hash"],
    )
    op.create_index(
        "ix_password_reset_codes_expires_at",
        "password_reset_codes",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_password_reset_codes_expires_at",
        table_name="password_reset_codes",
    )
    op.drop_index(
        "ix_password_reset_codes_code_hash",
        table_name="password_reset_codes",
    )
    op.drop_index(
        "ix_password_reset_codes_user_id",
        table_name="password_reset_codes",
    )
    op.drop_table("password_reset_codes")
