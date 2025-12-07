"""Add partial unique index for global notification preferences.

Revision ID: 20251207_124000
Revises: 20251207_120000
Create Date: 2025-12-07 12:40:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251207_124000"
down_revision = "20251207_120000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_user_notification_preferences_null_tenant",
        "user_notification_preferences",
        ["user_id", "channel", "category"],
        unique=True,
        postgresql_where=sa.text("tenant_id IS NULL"),
        sqlite_where=sa.text("tenant_id IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_user_notification_preferences_null_tenant",
        table_name="user_notification_preferences",
    )
