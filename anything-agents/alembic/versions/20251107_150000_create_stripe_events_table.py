"""create stripe events table

Revision ID: 20251107_150000
Revises: 20251106_235500_add_signing_kid_column
Create Date: 2025-11-07 15:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20251107_150000"
down_revision: str | None = "20251106_235500"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stripe_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("stripe_event_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("tenant_hint", sa.String(length=64), nullable=True),
        sa.Column("stripe_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_outcome", sa.String(length=32), server_default="received", nullable=False),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("processing_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_stripe_events_type", "stripe_events", ["event_type"])
    op.create_index("ix_stripe_events_status", "stripe_events", ["processing_outcome"])


def downgrade() -> None:
    op.drop_index("ix_stripe_events_status", table_name="stripe_events")
    op.drop_index("ix_stripe_events_type", table_name="stripe_events")
    op.drop_table("stripe_events")
