"""add unsubscribe token hash to status subscriptions"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251112_170000"
down_revision = "20251112_150000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "status_subscriptions",
        sa.Column("unsubscribe_token_hash", sa.String(length=128), nullable=True),
    )
    op.create_index(
        "ix_status_subscriptions_unsubscribe_hash",
        "status_subscriptions",
        ["unsubscribe_token_hash"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_status_subscriptions_unsubscribe_hash",
        table_name="status_subscriptions",
    )
    op.drop_column("status_subscriptions", "unsubscribe_token_hash")
