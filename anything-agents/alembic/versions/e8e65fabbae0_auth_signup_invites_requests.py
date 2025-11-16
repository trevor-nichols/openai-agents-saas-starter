"""Add signup invites and access request tables."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "e8e65fabbae0"
down_revision = "b9f552d26804"
branch_labels = None
depends_on = None


def upgrade() -> None:
    request_status_enum = postgresql.ENUM(
        "pending",
        "approved",
        "rejected",
        name="tenant_signup_request_status",
        create_type=False,
    )
    invite_status_enum = postgresql.ENUM(
        "active",
        "revoked",
        "expired",
        "exhausted",
        name="tenant_signup_invite_status",
        create_type=False,
    )
    reservation_status_enum = postgresql.ENUM(
        "active",
        "released",
        "finalized",
        "expired",
        name="signup_invite_reservation_status",
        create_type=False,
    )
    bind = op.get_bind()
    request_status_enum.create(bind, checkfirst=True)
    invite_status_enum.create(bind, checkfirst=True)
    reservation_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "tenant_signup_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("organization", sa.String(length=128), nullable=True),
        sa.Column("full_name", sa.String(length=128), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", request_status_enum, nullable=False, server_default="pending"),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("invite_token_hint", sa.String(length=16), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("honeypot_value", sa.String(length=64), nullable=True),
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.ForeignKeyConstraint(
            ["decided_by"],
            ["users.id"],
            name="fk_signup_requests_decided_by",
            ondelete="SET NULL",
        ),
    )

    op.create_index(
        "ix_tenant_signup_requests_status",
        "tenant_signup_requests",
        ["status"],
    )
    op.create_index(
        "ix_tenant_signup_requests_email",
        "tenant_signup_requests",
        ["email"],
    )

    op.create_table(
        "tenant_signup_invites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("token_hint", sa.String(length=16), nullable=False),
        sa.Column("invited_email", postgresql.CITEXT(), nullable=True),
        sa.Column("issuer_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("issuer_tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("signup_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", invite_status_enum, nullable=False, server_default="active"),
        sa.Column("max_redemptions", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("redeemed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_redeemed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.ForeignKeyConstraint(
            ["issuer_user_id"],
            ["users.id"],
            name="fk_signup_invites_issuer_user",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["issuer_tenant_id"],
            ["tenant_accounts.id"],
            name="fk_signup_invites_issuer_tenant",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["signup_request_id"],
            ["tenant_signup_requests.id"],
            name="fk_signup_invites_request",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("token_hash", name="uq_tenant_signup_invites_token_hash"),
    )

    op.create_index(
        "ix_tenant_signup_invites_status",
        "tenant_signup_invites",
        ["status"],
    )

    op.create_table(
        "tenant_signup_invite_reservations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("invite_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("status", reservation_status_enum, nullable=False, server_default="active"),
        sa.Column(
            "reserved_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_reason", sa.Text(), nullable=True),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
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
            ["invite_id"],
            ["tenant_signup_invites.id"],
            name="fk_invite_reservations_invite",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant_accounts.id"],
            name="fk_invite_reservations_tenant",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_invite_reservations_user",
            ondelete="SET NULL",
        ),
    )
    op.create_index(
        "ix_signup_invite_reservations_status",
        "tenant_signup_invite_reservations",
        ["status"],
    )
    op.create_index(
        "ix_signup_invite_reservations_invite_status",
        "tenant_signup_invite_reservations",
        ["invite_id", "status"],
    )
    op.create_index(
        "ix_signup_invite_reservations_expires",
        "tenant_signup_invite_reservations",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_signup_invite_reservations_expires",
        table_name="tenant_signup_invite_reservations",
    )
    op.drop_index(
        "ix_signup_invite_reservations_invite_status",
        table_name="tenant_signup_invite_reservations",
    )
    op.drop_index(
        "ix_signup_invite_reservations_status",
        table_name="tenant_signup_invite_reservations",
    )
    op.drop_table("tenant_signup_invite_reservations")
    op.drop_index("ix_tenant_signup_invites_status", table_name="tenant_signup_invites")
    op.drop_table("tenant_signup_invites")
    op.drop_index("ix_tenant_signup_requests_email", table_name="tenant_signup_requests")
    op.drop_index("ix_tenant_signup_requests_status", table_name="tenant_signup_requests")
    op.drop_table("tenant_signup_requests")

    bind = op.get_bind()
    invite_status_enum = postgresql.ENUM(
        "active",
        "revoked",
        "expired",
        "exhausted",
        name="tenant_signup_invite_status",
        create_type=False,
    )
    request_status_enum = postgresql.ENUM(
        "pending",
        "approved",
        "rejected",
        name="tenant_signup_request_status",
        create_type=False,
    )
    reservation_status_enum = postgresql.ENUM(
        "active",
        "released",
        "finalized",
        "expired",
        name="signup_invite_reservation_status",
        create_type=False,
    )
    invite_status_enum.drop(bind, checkfirst=True)
    request_status_enum.drop(bind, checkfirst=True)
    reservation_status_enum.drop(bind, checkfirst=True)
