"""Add agent_run_events table for full-fidelity conversation history."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "20251129_120000"
down_revision = "20251128_090000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_run_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("conversation_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("response_id", sa.String(length=128), nullable=True),
        sa.Column("run_item_type", sa.String(length=64), nullable=False),
        sa.Column("run_item_name", sa.String(length=128), nullable=True),
        sa.Column("role", sa.String(length=16), nullable=True),
        sa.Column("agent", sa.String(length=64), nullable=True),
        sa.Column("tool_call_id", sa.String(length=128), nullable=True),
        sa.Column("tool_name", sa.String(length=128), nullable=True),
        sa.Column("model", sa.String(length=64), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("reasoning_text", sa.Text(), nullable=True),
        sa.Column("call_arguments", pg.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("call_output", pg.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("attachments", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["agent_conversations.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("conversation_id", "sequence_no", name="uq_agent_run_events_seq"),
    )

    op.create_index(
        "ix_agent_run_events_conv_seq",
        "agent_run_events",
        ["conversation_id", "sequence_no"],
    )
    op.create_index(
        "ix_agent_run_events_toolcall",
        "agent_run_events",
        ["tool_call_id"],
    )
    op.create_index(
        "ix_agent_run_events_conv_type_seq",
        "agent_run_events",
        ["conversation_id", "run_item_type", "sequence_no"],
    )

    bind = op.get_bind()
    if bind and bind.dialect.name == "postgresql":
        op.create_index(
            "uq_agent_run_events_conv_resp_seq",
            "agent_run_events",
            [
                "conversation_id",
                "response_id",
                "sequence_no",
                "tool_call_id",
                "run_item_name",
            ],
            unique=True,
            postgresql_where=sa.text("response_id IS NOT NULL"),
        )
        op.create_index(
            "idx_agent_run_events_args_gin",
            "agent_run_events",
            ["call_arguments"],
            postgresql_using="gin",
        )
        op.create_index(
            "idx_agent_run_events_output_gin",
            "agent_run_events",
            ["call_output"],
            postgresql_using="gin",
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind and bind.dialect.name == "postgresql":
        op.drop_index("idx_agent_run_events_output_gin", table_name="agent_run_events")
        op.drop_index("idx_agent_run_events_args_gin", table_name="agent_run_events")
        op.drop_index("uq_agent_run_events_conv_resp_seq", table_name="agent_run_events")
    op.drop_index("ix_agent_run_events_conv_type_seq", table_name="agent_run_events")
    op.drop_index("ix_agent_run_events_toolcall", table_name="agent_run_events")
    op.drop_index("ix_agent_run_events_conv_seq", table_name="agent_run_events")
    op.drop_table("agent_run_events")
