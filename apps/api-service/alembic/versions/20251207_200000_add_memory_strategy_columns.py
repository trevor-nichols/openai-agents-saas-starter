"""Add memory strategy columns to agent_conversations

Revision ID: 20251207_200000
Revises: 20251207_180500
Create Date: 2025-12-07 20:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251207_200000"
down_revision = "20251207_180500"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agent_conversations", sa.Column("memory_strategy", sa.String(length=16), nullable=True))
    op.add_column("agent_conversations", sa.Column("memory_max_turns", sa.Integer(), nullable=True))
    op.add_column("agent_conversations", sa.Column("memory_keep_last_turns", sa.Integer(), nullable=True))
    op.add_column("agent_conversations", sa.Column("memory_compact_trigger_turns", sa.Integer(), nullable=True))
    op.add_column("agent_conversations", sa.Column("memory_compact_keep", sa.Integer(), nullable=True))
    op.add_column(
        "agent_conversations",
        sa.Column(
            "memory_clear_tool_inputs",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("agent_conversations", "memory_clear_tool_inputs")
    op.drop_column("agent_conversations", "memory_compact_keep")
    op.drop_column("agent_conversations", "memory_compact_trigger_turns")
    op.drop_column("agent_conversations", "memory_keep_last_turns")
    op.drop_column("agent_conversations", "memory_max_turns")
    op.drop_column("agent_conversations", "memory_strategy")
