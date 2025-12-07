"""Add MFA, consent, notification, usage, and security event tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251206_160000"
down_revision = ("fd0d6a8ba881", "b6dcb157d208")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums idempotently to avoid duplicate-object errors when migrations run twice.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mfa_method_type') THEN
                CREATE TYPE mfa_method_type AS ENUM ('totp', 'webauthn');
            END IF;
        END
        $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'usage_counter_granularity') THEN
                CREATE TYPE usage_counter_granularity AS ENUM ('day', 'month');
            END IF;
        END
        $$;
        """
    )

    mfa_enum = postgresql.ENUM(
        "totp",
        "webauthn",
        name="mfa_method_type",
        create_type=False,
    )
    usage_enum = postgresql.ENUM(
        "day",
        "month",
        name="usage_counter_granularity",
        create_type=False,
    )

    op.create_table(
        "user_mfa_methods",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("method_type", mfa_enum, nullable=False),
        sa.Column("label", sa.String(length=64), nullable=True),
        sa.Column("secret_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column(
            "credential_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.String(length=128), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "label", name="uq_user_mfa_methods_label"),
    )
    op.create_index(
        "ix_user_mfa_methods_user_type",
        "user_mfa_methods",
        ["user_id", "method_type"],
    )

    op.create_table(
        "user_recovery_codes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code_hash", sa.String(length=128), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_user_recovery_codes_user", "user_recovery_codes", ["user_id"])
    op.create_index("ix_user_recovery_codes_used", "user_recovery_codes", ["used_at"])

    op.create_table(
        "user_consents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("policy_key", sa.String(length=64), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column(
            "accepted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column("ip_hash", sa.String(length=128), nullable=True),
        sa.Column("user_agent_hash", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "policy_key", "version", name="uq_user_consents_version"),
    )
    op.create_index(
        "ix_user_consents_user_policy",
        "user_consents",
        ["user_id", "policy_key"],
    )

    op.create_table(
        "user_notification_preferences",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "user_id",
            "tenant_id",
            "channel",
            "category",
            name="uq_user_notification_preferences_scope",
        ),
    )
    op.create_index(
        "ix_user_notification_preferences_user",
        "user_notification_preferences",
        ["user_id"],
    )
    op.create_index(
        "ix_user_notification_preferences_tenant",
        "user_notification_preferences",
        ["tenant_id"],
    )

    op.create_table(
        "usage_counters",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("granularity", usage_enum, nullable=False),
        sa.Column("input_tokens", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("requests", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("storage_bytes", sa.BigInteger(), nullable=False, server_default="0"),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "tenant_id",
            "user_id",
            "period_start",
            "granularity",
            name="uq_usage_counters_bucket",
        ),
    )
    op.create_index(
        "ix_usage_counters_tenant_period",
        "usage_counters",
        ["tenant_id", "period_start"],
    )
    op.create_index(
        "ix_usage_counters_user_period",
        "usage_counters",
        ["user_id", "period_start"],
    )

    op.create_table(
        "security_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=True),
        sa.Column("ip_hash", sa.String(length=128), nullable=True),
        sa.Column("user_agent_hash", sa.String(length=128), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant_accounts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_security_events_user_created",
        "security_events",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_security_events_tenant_created",
        "security_events",
        ["tenant_id", "created_at"],
    )
    op.create_index("ix_security_events_type", "security_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_security_events_type", table_name="security_events")
    op.drop_index("ix_security_events_tenant_created", table_name="security_events")
    op.drop_index("ix_security_events_user_created", table_name="security_events")
    op.drop_table("security_events")

    op.drop_index("ix_usage_counters_user_period", table_name="usage_counters")
    op.drop_index("ix_usage_counters_tenant_period", table_name="usage_counters")
    op.drop_table("usage_counters")

    op.drop_index(
        "ix_user_notification_preferences_tenant",
        table_name="user_notification_preferences",
    )
    op.drop_index(
        "ix_user_notification_preferences_user",
        table_name="user_notification_preferences",
    )
    op.drop_table("user_notification_preferences")

    op.drop_index("ix_user_consents_user_policy", table_name="user_consents")
    op.drop_table("user_consents")

    op.drop_index("ix_user_recovery_codes_used", table_name="user_recovery_codes")
    op.drop_index("ix_user_recovery_codes_user", table_name="user_recovery_codes")
    op.drop_table("user_recovery_codes")

    op.drop_index("ix_user_mfa_methods_user_type", table_name="user_mfa_methods")
    op.drop_table("user_mfa_methods")

    # Drop enums last to satisfy dependencies.
    bind = op.get_bind()
    sa.Enum(name="usage_counter_granularity").drop(bind, checkfirst=True)
    sa.Enum(name="mfa_method_type").drop(bind, checkfirst=True)
