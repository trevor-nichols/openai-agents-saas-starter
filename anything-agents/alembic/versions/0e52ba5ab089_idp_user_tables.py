"""Add user auth tables for IDP milestone."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0e52ba5ab089"
down_revision = "20251106_235500"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    op.drop_constraint(
        "fk_agent_conversations_user_id_users",
        "agent_conversations",
        type_="foreignkey",
    )
    op.drop_table("users")

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'user_status'
            ) THEN
                CREATE TYPE user_status AS ENUM ('pending', 'active', 'disabled', 'locked');
            END IF;
        END
        $$;
        """
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("password_pepper_version", sa.String(length=32), nullable=False, server_default="v1"),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "active",
                "disabled",
                "locked",
                name="user_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
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
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_status", "users", ["status"])

    op.create_table(
        "user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=True),
        sa.Column("given_name", sa.String(length=64), nullable=True),
        sa.Column("family_name", sa.String(length=64), nullable=True),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.Column("locale", sa.String(length=32), nullable=True),
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
            ["user_id"],
            ["users.id"],
            name="fk_user_profiles_user_id_users",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id", name="uq_user_profiles_user_id"),
    )

    op.create_table(
        "tenant_user_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_tenant_user_memberships_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant_accounts.id"],
            name="fk_tenant_user_memberships_tenant_id_tenant_accounts",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "user_id",
            "tenant_id",
            name="uq_tenant_user_memberships_user_tenant",
        ),
    )
    op.create_index(
        "ix_tenant_user_memberships_tenant_role",
        "tenant_user_memberships",
        ["tenant_id", "role"],
    )
    op.create_index(
        "ix_tenant_user_memberships_user",
        "tenant_user_memberships",
        ["user_id"],
    )

    op.create_table(
        "password_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("password_pepper_version", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_password_history_user_id_users",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_password_history_user_created",
        "password_history",
        ["user_id", "created_at"],
    )

    op.create_table(
        "user_login_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ip_hash", sa.String(length=128), nullable=False),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("result", sa.String(length=16), nullable=False),
        sa.Column("reason", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_login_events_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant_accounts.id"],
            name="fk_user_login_events_tenant_id_tenant_accounts",
            ondelete="SET NULL",
        ),
    )
    op.create_index(
        "ix_user_login_events_user_created",
        "user_login_events",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_user_login_events_tenant_created",
        "user_login_events",
        ["tenant_id", "created_at"],
    )

    op.create_foreign_key(
        "fk_agent_conversations_user_id_users",
        "agent_conversations",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_agent_conversations_user_id_users",
        "agent_conversations",
        type_="foreignkey",
    )

    op.drop_index("ix_user_login_events_tenant_created", table_name="user_login_events")
    op.drop_index("ix_user_login_events_user_created", table_name="user_login_events")
    op.drop_table("user_login_events")

    op.drop_index("ix_password_history_user_created", table_name="password_history")
    op.drop_table("password_history")

    op.drop_index("ix_tenant_user_memberships_user", table_name="tenant_user_memberships")
    op.drop_index("ix_tenant_user_memberships_tenant_role", table_name="tenant_user_memberships")
    op.drop_table("tenant_user_memberships")

    op.drop_table("user_profiles")

    op.drop_index("ix_users_status", table_name="users")
    op.drop_constraint("uq_users_email", "users", type_="unique")
    op.drop_table("users")

    bind = op.get_bind()
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'user_status'
            ) THEN
                DROP TYPE user_status;
            END IF;
        END
        $$;
        """
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
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant_accounts.id"],
            name="fk_users_tenant_id_tenant_accounts",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "external_id",
            name="uq_users_tenant_external",
        ),
    )

    op.create_foreign_key(
        "fk_agent_conversations_user_id_users",
        "agent_conversations",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )
