"""Add provider conversation identifiers to agent conversations."""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251122_130000"
down_revision = "6724700351b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_conversations",
        sa.Column("provider", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "agent_conversations",
        sa.Column("provider_conversation_id", sa.String(length=128), nullable=True),
    )
    op.create_unique_constraint(
        "uq_agent_conversations_provider_conv_id",
        "agent_conversations",
        ["provider_conversation_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_agent_conversations_provider_conv_id",
        "agent_conversations",
        type_="unique",
    )
    op.drop_column("agent_conversations", "provider_conversation_id")
    op.drop_column("agent_conversations", "provider")
