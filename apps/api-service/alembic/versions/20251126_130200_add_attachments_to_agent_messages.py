"""add attachments column to agent_messages

Revision ID: 20251126_130200
Revises: 20251126_120000
Create Date: 2025-11-26 13:02:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251126_130200"
down_revision = "20251126_120000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_messages",
        sa.Column(
            "attachments",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
            server_default="[]",
        ),
    )
    op.execute("UPDATE agent_messages SET attachments = '[]' WHERE attachments IS NULL")


def downgrade() -> None:
    op.drop_column("agent_messages", "attachments")
