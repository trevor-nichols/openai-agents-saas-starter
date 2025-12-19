"""Make memory injection/clear flags nullable and drop defaults

Revision ID: 20251207_213000
Revises: 20251207_203000
Create Date: 2025-12-07 21:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251207_213000"
down_revision = "20251207_203000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop defaults and make nullable
    op.alter_column(
        "agent_conversations",
        "memory_injection",
        existing_type=sa.Boolean(),
        nullable=True,
        server_default=None,
    )
    op.alter_column(
        "agent_conversations",
        "memory_clear_tool_inputs",
        existing_type=sa.Boolean(),
        nullable=True,
        server_default=None,
    )

    # Clear implicit false overrides when no explicit memory settings exist
    op.execute(
        """
        UPDATE agent_conversations
        SET memory_injection = NULL
        WHERE memory_injection = false
          AND memory_strategy IS NULL
          AND memory_max_turns IS NULL
          AND memory_keep_last_turns IS NULL
          AND memory_compact_trigger_turns IS NULL
          AND memory_compact_keep IS NULL
          AND (memory_clear_tool_inputs IS NULL OR memory_clear_tool_inputs = false)
        """
    )
    op.execute(
        """
        UPDATE agent_conversations
        SET memory_clear_tool_inputs = NULL
        WHERE memory_clear_tool_inputs = false
          AND memory_strategy IS NULL
          AND memory_max_turns IS NULL
          AND memory_keep_last_turns IS NULL
          AND memory_compact_trigger_turns IS NULL
          AND memory_compact_keep IS NULL
        """
    )


def downgrade() -> None:
    op.alter_column(
        "agent_conversations",
        "memory_injection",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.text("false"),
    )
    op.alter_column(
        "agent_conversations",
        "memory_clear_tool_inputs",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.text("false"),
    )
