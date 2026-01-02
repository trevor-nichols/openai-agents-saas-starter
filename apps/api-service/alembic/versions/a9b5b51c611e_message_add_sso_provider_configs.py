"""Add SSO provider configs and user identity links."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a9b5b51c611e"
down_revision = "20251231_130000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tenant_role_enum = postgresql.ENUM(
        "owner",
        "admin",
        "member",
        "viewer",
        name="tenant_role",
        create_type=False,
        _create_events=False,
    )

    op.create_table(
        "sso_provider_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider_key", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("issuer_url", sa.String(length=512), nullable=False),
        sa.Column("client_id", sa.String(length=256), nullable=False),
        sa.Column("client_secret_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("discovery_url", sa.String(length=512), nullable=True),
        sa.Column("scopes_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("pkce_required", sa.Boolean(), nullable=False),
        sa.Column(
            "token_endpoint_auth_method",
            sa.String(length=64),
            nullable=False,
            server_default="client_secret_post",
        ),
        sa.Column(
            "allowed_id_token_algs_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "auto_provision_policy",
            sa.Enum(
                "disabled",
                "invite_only",
                "domain_allowlist",
                name="sso_auto_provision_policy",
            ),
            nullable=False,
        ),
        sa.Column("allowed_domains_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "default_role",
            tenant_role_enum,
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant_accounts.id"],
            name=op.f("fk_sso_provider_configs_tenant_id_tenant_accounts"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sso_provider_configs")),
        sa.UniqueConstraint(
            "tenant_id",
            "provider_key",
            name="uq_sso_provider_configs_tenant_provider",
        ),
    )
    op.create_index(
        "ix_sso_provider_configs_global_provider",
        "sso_provider_configs",
        ["provider_key"],
        unique=True,
        postgresql_where=sa.text("tenant_id IS NULL"),
    )
    op.create_index(
        "ix_sso_provider_configs_provider_key",
        "sso_provider_configs",
        ["provider_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sso_provider_configs_tenant_id"),
        "sso_provider_configs",
        ["tenant_id"],
        unique=False,
    )

    op.create_table(
        "user_identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_key", sa.String(length=64), nullable=False),
        sa.Column("issuer", sa.String(length=512), nullable=False),
        sa.Column("subject", sa.String(length=256), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("email_verified", sa.Boolean(), nullable=False),
        sa.Column("profile_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_identities_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_identities")),
        sa.UniqueConstraint(
            "provider_key",
            "issuer",
            "subject",
            name="uq_user_identities_provider_subject",
        ),
        sa.UniqueConstraint(
            "user_id",
            "provider_key",
            name="uq_user_identities_user_provider",
        ),
    )
    op.create_index(
        "ix_user_identities_user_id",
        "user_identities",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_identities_user_id", table_name="user_identities")
    op.drop_table("user_identities")

    op.drop_index(
        "ix_sso_provider_configs_global_provider",
        table_name="sso_provider_configs",
    )
    op.drop_index(
        "ix_sso_provider_configs_provider_key",
        table_name="sso_provider_configs",
    )
    op.drop_index(op.f("ix_sso_provider_configs_tenant_id"), table_name="sso_provider_configs")
    op.drop_table("sso_provider_configs")

    sa.Enum(
        "disabled",
        "invite_only",
        "domain_allowlist",
        name="sso_auto_provision_policy",
    ).drop(op.get_bind(), checkfirst=True)
