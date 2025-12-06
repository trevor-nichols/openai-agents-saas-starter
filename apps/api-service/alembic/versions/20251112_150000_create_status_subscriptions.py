"""create status subscriptions table"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251112_150000"
down_revision = "1409f49e60f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "status_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("target_hash", sa.String(length=128), nullable=False),
        sa.Column("target_masked", sa.String(length=512), nullable=False),
        sa.Column("target_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column(
            "severity_filter",
            sa.String(length=16),
            nullable=False,
            server_default="major",
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="pending_verification",
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("verification_token_hash", sa.String(length=128), nullable=True),
        sa.Column("verification_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("challenge_token_hash", sa.String(length=128), nullable=True),
        sa.Column("webhook_secret_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("revoked_reason", sa.Text(), nullable=True),
        sa.Column("last_challenge_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_status_subscriptions_target_hash",
        "status_subscriptions",
        ["target_hash"],
    )
    op.create_index(
        "ix_status_subscriptions_verification_hash",
        "status_subscriptions",
        ["verification_token_hash"],
    )
    op.create_index(
        "ix_status_subscriptions_challenge_hash",
        "status_subscriptions",
        ["challenge_token_hash"],
    )
    op.create_index(
        "ix_status_subscriptions_tenant_id",
        "status_subscriptions",
        ["tenant_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_status_subscriptions_tenant_id", table_name="status_subscriptions")
    op.drop_index("ix_status_subscriptions_challenge_hash", table_name="status_subscriptions")
    op.drop_index("ix_status_subscriptions_verification_hash", table_name="status_subscriptions")
    op.drop_index("ix_status_subscriptions_target_hash", table_name="status_subscriptions")
    op.drop_table("status_subscriptions")
