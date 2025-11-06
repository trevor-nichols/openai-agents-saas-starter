"""create conversation and billing tables"""

from __future__ import annotations

import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251106_120000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(length=64), nullable=False, unique=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
    )

    op.create_table(
        "billing_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("interval", sa.String(length=16), nullable=False, server_default="monthly"),
        sa.Column("interval_count", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("trial_days", sa.Integer(), nullable=True),
        sa.Column("seat_included", sa.Integer(), nullable=True),
        sa.Column("feature_toggles", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.UniqueConstraint("code", name="uq_billing_plans_code"),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant_accounts.id"],
            name="fk_users_tenant_id_tenant_accounts",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("tenant_id", "external_id", name="uq_users_tenant_external"),
    )

    op.create_table(
        "plan_features",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feature_key", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("hard_limit", sa.Integer(), nullable=True),
        sa.Column("soft_limit", sa.Integer(), nullable=True),
        sa.Column(
            "is_metered",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("timezone('utc', now())"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["billing_plans.id"],
            name="fk_plan_features_plan_id_billing_plans",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("plan_id", "feature_key", name="uq_plan_features_plan_feature"),
    )

    op.create_table(
        "tenant_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="active"),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("billing_email", sa.String(length=256), nullable=True),
        sa.Column("processor", sa.String(length=32), nullable=True),
        sa.Column("processor_customer_id", sa.String(length=128), nullable=True),
        sa.Column("processor_subscription_id", sa.String(length=128), nullable=True),
        sa.Column(
            "starts_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("seat_count", sa.Integer(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant_accounts.id"],
            name="fk_tenant_subscriptions_tenant_id_tenant_accounts",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["billing_plans.id"],
            name="fk_tenant_subscriptions_plan_id_billing_plans",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "status",
            name="uq_tenant_subscriptions_active",
            deferrable=True,
            initially="IMMEDIATE",
        ),
    )
    op.create_index(
        "ix_tenant_subscriptions_tenant_status",
        "tenant_subscriptions",
        ["tenant_id", "status"],
    )

    op.create_table(
        "subscription_invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="draft"),
        sa.Column("external_invoice_id", sa.String(length=128), nullable=True),
        sa.Column("hosted_invoice_url", sa.String(length=256), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["tenant_subscriptions.id"],
            name="fk_subscription_invoices_subscription_id_tenant_subscriptions",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_subscription_invoices_subscription_period",
        "subscription_invoices",
        ["subscription_id", "period_start"],
    )

    op.create_table(
        "subscription_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feature_key", sa.String(length=64), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column(
            "reported_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column("external_event_id", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["tenant_subscriptions.id"],
            name="fk_subscription_usage_subscription_id_tenant_subscriptions",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "subscription_id",
            "feature_key",
            "period_start",
            name="uq_subscription_usage_feature_period",
        ),
    )

    op.create_table(
        "agent_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_key", sa.String(length=255), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("agent_entrypoint", sa.String(length=64), nullable=False),
        sa.Column("active_agent", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "total_tokens_prompt",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "total_tokens_completion",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "reasoning_tokens",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("handoff_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("source_channel", sa.String(length=32), nullable=True),
        sa.Column("topic_hint", sa.String(length=256), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_id", sa.String(length=64), nullable=True),
        sa.Column("client_version", sa.String(length=32), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant_accounts.id"],
            name="fk_agent_conversations_tenant_id_tenant_accounts",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_agent_conversations_user_id_users",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("conversation_key", name="uq_agent_conversations_key"),
    )
    op.create_index(
        "ix_agent_conversations_tenant_updated",
        "agent_conversations",
        ["tenant_id", "updated_at"],
    )
    op.create_index(
        "ix_agent_conversations_tenant_status",
        "agent_conversations",
        ["tenant_id", "status"],
    )

    op.create_table(
        "agent_messages",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("agent_type", sa.String(length=64), nullable=True),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=True),
        sa.Column("tool_call_id", sa.String(length=64), nullable=True),
        sa.Column("token_count_prompt", sa.Integer(), nullable=True),
        sa.Column("token_count_completion", sa.Integer(), nullable=True),
        sa.Column("reasoning_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("content_checksum", sa.String(length=32), nullable=True),
        sa.Column("run_id", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["agent_conversations.id"],
            name="fk_agent_messages_conversation_id_agent_conversations",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "conversation_id",
            "position",
            name="uq_agent_messages_conversation_position",
        ),
    )
    op.create_index(
        "ix_agent_messages_conversation_created",
        "agent_messages",
        ["conversation_id", "created_at"],
    )

    seed_default_plans()


def seed_default_plans() -> None:
    """Seed baseline billing plans to support local testing."""

    plans_table = sa.table(
        "billing_plans",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("interval", sa.String),
        sa.column("interval_count", sa.Integer),
        sa.column("price_cents", sa.Integer),
        sa.column("currency", sa.String),
        sa.column("trial_days", sa.Integer),
        sa.column("seat_included", sa.Integer),
        sa.column("feature_toggles", postgresql.JSONB),
        sa.column("is_active", sa.Boolean),
    )

    starter_plan_id = uuid.uuid4()
    pro_plan_id = uuid.uuid4()

    op.bulk_insert(
        plans_table,
        [
            {
                "id": starter_plan_id,
                "code": "starter",
                "name": "Starter",
                "interval": "monthly",
                "interval_count": 1,
                "price_cents": 0,
                "currency": "USD",
                "trial_days": 14,
                "seat_included": 1,
                "feature_toggles": {"enable_web_search": False},
                "is_active": True,
            },
            {
                "id": pro_plan_id,
                "code": "pro",
                "name": "Pro",
                "interval": "monthly",
                "interval_count": 1,
                "price_cents": 9900,
                "currency": "USD",
                "trial_days": 14,
                "seat_included": 5,
                "feature_toggles": {"enable_web_search": True},
                "is_active": True,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_agent_messages_conversation_created", table_name="agent_messages")
    op.drop_table("agent_messages")

    op.drop_index("ix_agent_conversations_tenant_status", table_name="agent_conversations")
    op.drop_index("ix_agent_conversations_tenant_updated", table_name="agent_conversations")
    op.drop_table("agent_conversations")

    op.drop_table("subscription_usage")
    op.drop_index(
        "ix_subscription_invoices_subscription_period",
        table_name="subscription_invoices",
    )
    op.drop_table("subscription_invoices")

    op.drop_index(
        "ix_tenant_subscriptions_tenant_status",
        table_name="tenant_subscriptions",
    )
    op.drop_table("tenant_subscriptions")

    op.drop_table("plan_features")
    op.drop_table("users")
    op.drop_table("billing_plans")
    op.drop_table("tenant_accounts")
