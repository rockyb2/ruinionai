"""Add meeting participants and in-app meeting invitations.

Revision ID: d27f6b8a910c
Revises: c18e72a90f31
"""
from alembic import op
import sqlalchemy as sa


revision = "d27f6b8a910c"
down_revision = "c18e72a90f31"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "meeting_participants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("meeting_id", sa.Integer(), sa.ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("member_id", sa.Integer(), sa.ForeignKey("organization_members.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("meeting_id", "member_id", name="uq_meeting_participants_meeting_member"),
    )
    op.create_index("ix_meeting_participants_meeting_id", "meeting_participants", ["meeting_id"])
    op.create_index("ix_meeting_participants_member_id", "meeting_participants", ["member_id"])
    op.add_column("organization_notifications", sa.Column("meeting_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_organization_notifications_meeting_id", "organization_notifications", "meetings",
        ["meeting_id"], ["id"], ondelete="CASCADE",
    )
    op.create_index("ix_organization_notifications_meeting_id", "organization_notifications", ["meeting_id"])
    op.create_unique_constraint(
        "uq_organization_notifications_user_kind_meeting",
        "organization_notifications", ["user_id", "kind", "meeting_id"],
    )


def downgrade():
    op.drop_constraint("uq_organization_notifications_user_kind_meeting", "organization_notifications", type_="unique")
    op.drop_index("ix_organization_notifications_meeting_id", table_name="organization_notifications")
    op.drop_constraint("fk_organization_notifications_meeting_id", "organization_notifications", type_="foreignkey")
    op.drop_column("organization_notifications", "meeting_id")
    op.drop_table("meeting_participants")
