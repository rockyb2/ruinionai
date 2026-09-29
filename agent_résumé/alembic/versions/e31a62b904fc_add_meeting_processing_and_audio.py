"""Durable meeting queue and audio history.

Revision ID: e31a62b904fc
Revises: d27f6b8a910c
"""
from alembic import op
import sqlalchemy as sa

revision = "e31a62b904fc"
down_revision = "d27f6b8a910c"
branch_labels = None
depends_on = None


def upgrade():
    for name, kind in [
        ("audio_manifest", sa.JSON()), ("audio_path", sa.String()),
        ("audio_duration", sa.Float()), ("transcription_segments", sa.JSON()),
        ("processing_error", sa.Text()), ("processing_token", sa.String(36)),
        ("processing_expires_at", sa.DateTime()),
    ]:
        op.add_column("meetings", sa.Column(name, kind, nullable=True))
    op.add_column("meetings", sa.Column("processing_status", sa.String(24), nullable=False, server_default="idle"))
    op.create_index("ix_meetings_processing_status", "meetings", ["processing_status"])
    op.execute("UPDATE meetings SET processing_status = 'completed' WHERE report_path IS NOT NULL AND summary_short IS NOT NULL AND summary_long IS NOT NULL")


def downgrade():
    op.drop_index("ix_meetings_processing_status", table_name="meetings")
    for name in ["audio_manifest", "audio_path", "audio_duration", "transcription_segments", "processing_status", "processing_error", "processing_token", "processing_expires_at"]:
        op.drop_column("meetings", name)
