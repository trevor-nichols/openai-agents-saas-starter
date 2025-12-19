"""Add summary_length_tokens to conversation_summaries."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20251208_090000"
down_revision = "20251207_230000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversation_summaries",
        sa.Column("summary_length_tokens", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("conversation_summaries", "summary_length_tokens")
