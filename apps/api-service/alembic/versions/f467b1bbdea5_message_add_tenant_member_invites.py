"""Add tenant member invites table."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "f467b1bbdea5"
down_revision = "e8a40a39b480"
branch_labels = None
depends_on = None


def upgrade() -> None:
    invite_status_enum = postgresql.ENUM(
        "active",
        "accepted",
        "revoked",
        "expired",
        name="tenant_member_invite_status",
        create_type=False,
    )
    invite_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "tenant_member_invites",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("token_hint", sa.String(length=16), nullable=False),
        sa.Column("invited_email", postgresql.CITEXT(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column(
            "status",
            invite_status_enum,
            nullable=False,
            server_default="active",
        ),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("accepted_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
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
            name="fk_tenant_member_invites_tenant_id_tenant_accounts",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            name="fk_tenant_member_invites_created_by_user_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["accepted_by_user_id"],
            ["users.id"],
            name="fk_tenant_member_invites_accepted_by_user_id_users",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("token_hash", name="uq_tenant_member_invites_token_hash"),
    )
    op.create_index(
        "ix_tenant_member_invites_email",
        "tenant_member_invites",
        ["invited_email"],
    )
    op.create_index(
        "ix_tenant_member_invites_tenant_status",
        "tenant_member_invites",
        ["tenant_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_tenant_member_invites_tenant_status", table_name="tenant_member_invites")
    op.drop_index("ix_tenant_member_invites_email", table_name="tenant_member_invites")
    op.drop_table("tenant_member_invites")

    bind = op.get_bind()
    invite_status_enum = postgresql.ENUM(
        "active",
        "accepted",
        "revoked",
        "expired",
        name="tenant_member_invite_status",
        create_type=False,
    )
    invite_status_enum.drop(bind, checkfirst=True)
