"""add encrypted unsubscribe token column"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251112_200500"
down_revision = "20251112_170000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "status_subscriptions",
        sa.Column("unsubscribe_token_encrypted", sa.LargeBinary(), nullable=True),
    )



def downgrade() -> None:
    op.drop_column("status_subscriptions", "unsubscribe_token_encrypted")
