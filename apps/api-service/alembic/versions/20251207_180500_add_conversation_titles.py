"""Add display_name and title_generated_at to conversations

Revision ID: 20251207_180500
Revises: 20251207_124000
Create Date: 2025-12-07 18:05:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251207_180500"
down_revision = "20251207_124000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_conversations",
        sa.Column("display_name", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "agent_conversations",
        sa.Column("title_generated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("agent_conversations", "title_generated_at")
    op.drop_column("agent_conversations", "display_name")
