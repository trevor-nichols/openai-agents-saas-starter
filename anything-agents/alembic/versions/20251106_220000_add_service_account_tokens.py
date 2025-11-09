"""Add service_account_tokens table for refresh token reuse."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251106_220000"
down_revision = "20251106_120000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "service_account_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account", sa.String(length=128), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scope_key", sa.String(length=256), nullable=False),
        sa.Column("scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=False),
        sa.Column("refresh_jti", sa.String(length=64), nullable=False),
        sa.Column("fingerprint", sa.String(length=128), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("refresh_jti", name="uq_service_account_tokens_jti"),
    )
    op.create_index(
        "ix_service_account_tokens_tenant",
        "service_account_tokens",
        ["tenant_id"],
    )
    op.create_index(
        "ix_service_account_tokens_scope_key",
        "service_account_tokens",
        ["scope_key"],
    )
    op.create_index(
        "uq_service_account_tokens_active_key",
        "service_account_tokens",
        ["account", "tenant_id", "scope_key"],
        unique=True,
        postgresql_where=sa.text("revoked_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_service_account_tokens_active_key", table_name="service_account_tokens")
    op.drop_index("ix_service_account_tokens_scope_key", table_name="service_account_tokens")
    op.drop_index("ix_service_account_tokens_tenant", table_name="service_account_tokens")
    op.drop_table("service_account_tokens")
