"""Add durable conversation ledger tables for exact UI replay.

Revision ID: 45b781fda5df
Revises: 20251208_090000
Create Date: 2025-12-17
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "45b781fda5df"
down_revision = "20251208_090000"
branch_labels = None
depends_on = None


def _utcnow_default() -> sa.TextClause:
    """Return a cross-dialect 'now' expression compatible with SQLite and Postgres."""

    bind = op.get_bind()
    if bind is not None and bind.dialect.name == "sqlite":
        return sa.text("CURRENT_TIMESTAMP")
    return sa.text("timezone('utc', now())")


def upgrade() -> None:
    utc_now = _utcnow_default()
    uuid_type = postgresql.UUID(as_uuid=True)

    op.create_table(
        "conversation_ledger_segments",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column(
            "tenant_id",
            uuid_type,
            sa.ForeignKey("tenant_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            uuid_type,
            sa.ForeignKey("agent_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("segment_index", sa.Integer(), nullable=False),
        sa.Column(
            "parent_segment_id",
            uuid_type,
            sa.ForeignKey("conversation_ledger_segments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("visible_through_event_id", sa.BigInteger(), nullable=True),
        sa.Column("truncated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=utc_now, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=utc_now, nullable=False),
        sa.UniqueConstraint(
            "conversation_id",
            "segment_index",
            name="uq_conversation_ledger_segments_conversation_index",
        ),
    )
    op.create_index(
        "ix_conversation_ledger_segments_conversation_truncated",
        "conversation_ledger_segments",
        ["conversation_id", "truncated_at"],
    )

    op.create_table(
        "conversation_ledger_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "tenant_id",
            uuid_type,
            sa.ForeignKey("tenant_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            uuid_type,
            sa.ForeignKey("agent_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "segment_id",
            uuid_type,
            sa.ForeignKey("conversation_ledger_segments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "schema_version",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'public_sse_v1'"),
        ),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("stream_id", sa.String(length=255), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("server_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("response_id", sa.String(length=128), nullable=True),
        sa.Column("agent", sa.String(length=64), nullable=True),
        sa.Column("workflow_run_id", sa.String(length=64), nullable=True),
        sa.Column("provider_sequence_number", sa.Integer(), nullable=True),
        sa.Column("output_index", sa.Integer(), nullable=True),
        sa.Column("item_id", sa.String(length=255), nullable=True),
        sa.Column("content_index", sa.Integer(), nullable=True),
        sa.Column("tool_call_id", sa.String(length=255), nullable=True),
        sa.Column("payload_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "payload_object_id",
            uuid_type,
            sa.ForeignKey("storage_objects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=utc_now, nullable=False),
        sa.CheckConstraint(
            "payload_json IS NOT NULL OR payload_object_id IS NOT NULL",
            name="ck_conversation_ledger_events_payload_present",
        ),
        sa.UniqueConstraint(
            "conversation_id",
            "stream_id",
            "event_id",
            name="uq_conversation_ledger_events_conversation_stream_event",
        ),
    )
    op.create_index(
        "ix_conversation_ledger_events_item_id",
        "conversation_ledger_events",
        ["item_id"],
    )
    op.create_index(
        "ix_conversation_ledger_events_tool_call_id",
        "conversation_ledger_events",
        ["tool_call_id"],
    )
    op.create_index(
        "ix_conversation_ledger_events_tenant_conversation_id_id",
        "conversation_ledger_events",
        ["tenant_id", "conversation_id", "id"],
    )

    op.create_table(
        "conversation_run_queue_items",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "tenant_id",
            uuid_type,
            sa.ForeignKey("tenant_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            uuid_type,
            sa.ForeignKey("agent_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "segment_id",
            uuid_type,
            sa.ForeignKey("conversation_ledger_segments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by_user_id",
            uuid_type,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'queued'"),
        ),
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("error_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=utc_now, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_conversation_run_queue_items_conversation_status_id",
        "conversation_run_queue_items",
        ["conversation_id", "status", "id"],
    )
    op.create_index(
        "ix_conversation_run_queue_items_tenant_conversation_status_id",
        "conversation_run_queue_items",
        ["tenant_id", "conversation_id", "status", "id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_conversation_run_queue_items_tenant_conversation_status_id",
        table_name="conversation_run_queue_items",
    )
    op.drop_index(
        "ix_conversation_run_queue_items_conversation_status_id",
        table_name="conversation_run_queue_items",
    )
    op.drop_table("conversation_run_queue_items")

    op.drop_index(
        "ix_conversation_ledger_events_tenant_conversation_id_id",
        table_name="conversation_ledger_events",
    )
    op.drop_index(
        "ix_conversation_ledger_events_tool_call_id",
        table_name="conversation_ledger_events",
    )
    op.drop_index(
        "ix_conversation_ledger_events_item_id",
        table_name="conversation_ledger_events",
    )
    op.drop_table("conversation_ledger_events")

    op.drop_index(
        "ix_conversation_ledger_segments_conversation_truncated",
        table_name="conversation_ledger_segments",
    )
    op.drop_table("conversation_ledger_segments")
