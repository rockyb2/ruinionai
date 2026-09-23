"""add organization settings and notifications

Revision ID: c18e72a90f31
Revises: ebea4dc47b12
Create Date: 2026-09-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c18e72a90f31"
down_revision: Union[str, Sequence[str], None] = "ebea4dc47b12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "organizations",
        sa.Column(
            "invitation_expiration_days",
            sa.Integer(),
            server_default="7",
            nullable=False,
        ),
    )
    op.add_column(
        "organizations",
        sa.Column(
            "allow_admin_invitations",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
    )
    op.add_column(
        "organizations",
        sa.Column(
            "invitation_notifications_enabled",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_organizations_invitation_expiration_days",
        "organizations",
        "invitation_expiration_days BETWEEN 1 AND 30",
    )

    op.create_table(
        "organization_notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("invitation_id", sa.Integer(), nullable=True),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["invitation_id"],
            ["organization_invitations.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "kind",
            "invitation_id",
            name="uq_organization_notifications_user_kind_invitation",
        ),
    )
    op.create_index(
        op.f("ix_organization_notifications_id"),
        "organization_notifications",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_organization_notifications_organization_id"),
        "organization_notifications",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_organization_notifications_user_id"),
        "organization_notifications",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_organization_notifications_invitation_id"),
        "organization_notifications",
        ["invitation_id"],
        unique=False,
    )

    # Les anciennes organisations n'avaient pas le rôle owner.
    # Pour chaque organisation sans owner, le membre actif le plus ancien
    # devient propriétaire. Un ancien admin est choisi avant un membre simple.
    op.execute(
        """
        WITH ranked_candidates AS (
            SELECT
                membership.id,
                membership.organization_id,
                ROW_NUMBER() OVER (
                    PARTITION BY membership.organization_id
                    ORDER BY
                        CASE WHEN membership.role::text = 'admin' THEN 0 ELSE 1 END,
                        membership.created_at ASC NULLS LAST,
                        membership.id ASC
                ) AS position
            FROM organization_members AS membership
            WHERE membership.status::text = 'active'
              AND NOT EXISTS (
                  SELECT 1
                  FROM organization_members AS current_owner
                  WHERE current_owner.organization_id = membership.organization_id
                    AND current_owner.role::text = 'owner'
              )
        )
        UPDATE organization_members AS membership
        SET role = 'owner'::organization_member_role,
            updated_at = CURRENT_TIMESTAMP
        FROM ranked_candidates AS candidate
        WHERE membership.id = candidate.id
          AND candidate.position = 1
        """
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_organization_notifications_invitation_id"),
        table_name="organization_notifications",
    )
    op.drop_index(
        op.f("ix_organization_notifications_user_id"),
        table_name="organization_notifications",
    )
    op.drop_index(
        op.f("ix_organization_notifications_organization_id"),
        table_name="organization_notifications",
    )
    op.drop_index(
        op.f("ix_organization_notifications_id"),
        table_name="organization_notifications",
    )
    op.drop_table("organization_notifications")

    op.drop_constraint(
        "ck_organizations_invitation_expiration_days",
        "organizations",
        type_="check",
    )
    op.drop_column("organizations", "invitation_notifications_enabled")
    op.drop_column("organizations", "allow_admin_invitations")
    op.drop_column("organizations", "invitation_expiration_days")
    op.drop_column("organizations", "description")
