"""Add conversation summaries table and memory injection flag

Revision ID: 20251207_203000
Revises: 20251207_200000
Create Date: 2025-12-07 20:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251207_203000"
down_revision = "20251207_200000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_conversations",
        sa.Column(
            "memory_injection",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.create_table(
        "conversation_summaries",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_key", sa.String(length=64), nullable=True),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("summary_model", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("timezone('utc', now())"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["agent_conversations.id"], ondelete="CASCADE"),
        sa.Index("ix_conversation_summaries_lookup", "tenant_id", "conversation_id", "agent_key", "created_at"),
    )


def downgrade() -> None:
    op.drop_table("conversation_summaries")
    op.drop_column("agent_conversations", "memory_injection")
