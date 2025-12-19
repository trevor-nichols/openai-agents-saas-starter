"""add agent_run_usage table and cached token aggregates

Revision ID: 20251207_230000
Revises: 20251207_203000
Create Date: 2025-12-07 23:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251207_230000"
down_revision = "20251207_213000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_conversations",
        sa.Column("total_cached_input_tokens", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "agent_conversations",
        sa.Column("total_requests", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "agent_run_usage",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("response_id", sa.String(length=128), nullable=True),
        sa.Column("run_id", sa.String(length=64), nullable=True),
        sa.Column("agent_key", sa.String(length=64), nullable=True),
        sa.Column("provider", sa.String(length=32), nullable=True),
        sa.Column("requests", sa.Integer(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("cached_input_tokens", sa.Integer(), nullable=True),
        sa.Column("reasoning_output_tokens", sa.Integer(), nullable=True),
        sa.Column("request_usage_entries", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.UniqueConstraint("response_id", name="uq_agent_run_usage_response_id"),
    )

    op.create_index(
        "ix_agent_run_usage_conversation_created",
        "agent_run_usage",
        ["conversation_id", "created_at"],
    )
    op.create_index(
        "ix_agent_run_usage_tenant_created",
        "agent_run_usage",
        ["tenant_id", "created_at"],
    )
    op.create_index(
        "ix_agent_run_usage_response",
        "agent_run_usage",
        ["response_id"],
    )

    # Drop server defaults to keep runtime semantics unchanged after backfill
    op.alter_column(
        "agent_conversations",
        "total_cached_input_tokens",
        server_default=None,
        existing_type=sa.Integer(),
    )
    op.alter_column(
        "agent_conversations",
        "total_requests",
        server_default=None,
        existing_type=sa.Integer(),
    )


def downgrade() -> None:
    op.drop_index("ix_agent_run_usage_response", table_name="agent_run_usage")
    op.drop_index("ix_agent_run_usage_tenant_created", table_name="agent_run_usage")
    op.drop_index("ix_agent_run_usage_conversation_created", table_name="agent_run_usage")
    op.drop_table("agent_run_usage")

    op.drop_column("agent_conversations", "total_requests")
    op.drop_column("agent_conversations", "total_cached_input_tokens")
