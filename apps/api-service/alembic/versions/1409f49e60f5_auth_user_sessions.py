"""Add user session telemetry + multi-device support."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "1409f49e60f5"
down_revision = "bcb7e73b5f7b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("refresh_jti", sa.String(length=64), nullable=False, unique=True),
        sa.Column("fingerprint", sa.String(length=256), nullable=True),
        sa.Column("ip_hash", sa.String(length=128), nullable=True),
        sa.Column("ip_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("ip_masked", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("client_platform", sa.String(length=64), nullable=True),
        sa.Column("client_browser", sa.String(length=64), nullable=True),
        sa.Column("client_device", sa.String(length=32), nullable=True),
        sa.Column("location_city", sa.String(length=128), nullable=True),
        sa.Column("location_region", sa.String(length=128), nullable=True),
        sa.Column("location_country", sa.String(length=64), nullable=True),
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
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.String(length=256), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_sessions_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant_accounts.id"],
            name="fk_user_sessions_tenant_id_tenant_accounts",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_user_sessions_user_last_seen",
        "user_sessions",
        ["user_id", "last_seen_at"],
    )
    op.create_index(
        "ix_user_sessions_tenant_last_seen",
        "user_sessions",
        ["tenant_id", "last_seen_at"],
    )
    op.create_index(
        "ix_user_sessions_refresh_jti",
        "user_sessions",
        ["refresh_jti"],
        unique=True,
    )
    op.create_index(
        "ix_user_sessions_fingerprint",
        "user_sessions",
        ["user_id", "fingerprint"],
    )

    op.add_column(
        "service_account_tokens",
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_service_account_tokens_session_id_user_sessions",
        "service_account_tokens",
        "user_sessions",
        ["session_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_index(
        "uq_service_account_tokens_active_key",
        table_name="service_account_tokens",
    )
    op.create_index(
        "uq_service_account_tokens_active_service_accounts",
        "service_account_tokens",
        ["account", "tenant_id", "scope_key"],
        unique=True,
        postgresql_where=sa.text("revoked_at IS NULL AND account NOT LIKE 'user:%'"),
    )
    op.create_index(
        "ix_service_account_tokens_session_id",
        "service_account_tokens",
        ["session_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_service_account_tokens_session_id",
        table_name="service_account_tokens",
    )
    op.drop_index(
        "uq_service_account_tokens_active_service_accounts",
        table_name="service_account_tokens",
    )
    op.create_index(
        "uq_service_account_tokens_active_key",
        "service_account_tokens",
        ["account", "tenant_id", "scope_key"],
        unique=True,
        postgresql_where=sa.text("revoked_at IS NULL"),
    )
    op.drop_constraint(
        "fk_service_account_tokens_session_id_user_sessions",
        "service_account_tokens",
        type_="foreignkey",
    )
    op.drop_column("service_account_tokens", "session_id")

    op.drop_index("ix_user_sessions_fingerprint", table_name="user_sessions")
    op.drop_index("ix_user_sessions_refresh_jti", table_name="user_sessions")
    op.drop_index("ix_user_sessions_tenant_last_seen", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user_last_seen", table_name="user_sessions")
    op.drop_table("user_sessions")
