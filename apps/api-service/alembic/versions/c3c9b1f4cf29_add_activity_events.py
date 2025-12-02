"""Add activity_events table

Revision ID: c3c9b1f4cf29
Revises: 4f9a8c7e3b4d
Create Date: 2025-12-01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "c3c9b1f4cf29"
down_revision = "4f9a8c7e3b4d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "activity_events",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=96), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("actor_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_type", sa.String(length=16), nullable=True),
        sa.Column("actor_role", sa.String(length=32), nullable=True),
        sa.Column("object_type", sa.String(length=64), nullable=True),
        sa.Column("object_id", sa.String(length=128), nullable=True),
        sa.Column("object_name", sa.String(length=256), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="success"),
        sa.Column("source", sa.String(length=32), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("ip_hash", sa.String(length=128), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant_accounts.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_activity_events_tenant_created",
        "activity_events",
        ["tenant_id", "created_at"],
    )
    op.create_index(
        "ix_activity_events_tenant_action",
        "activity_events",
        ["tenant_id", "action"],
    )
    op.create_index(
        "ix_activity_events_object",
        "activity_events",
        ["tenant_id", "object_type", "object_id"],
    )
    op.create_index(
        "ix_activity_events_request",
        "activity_events",
        ["request_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_activity_events_request", table_name="activity_events")
    op.drop_index("ix_activity_events_object", table_name="activity_events")
    op.drop_index("ix_activity_events_tenant_action", table_name="activity_events")
    op.drop_index("ix_activity_events_tenant_created", table_name="activity_events")
    op.drop_table("activity_events")
