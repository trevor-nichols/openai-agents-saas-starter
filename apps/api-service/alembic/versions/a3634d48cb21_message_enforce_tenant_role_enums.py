"""Enforce tenant role enums and add platform role column."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "a3634d48cb21"
down_revision = "f467b1bbdea5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tenant_role_enum = postgresql.ENUM(
        "viewer",
        "member",
        "admin",
        "owner",
        name="tenant_role",
        create_type=False,
    )
    tenant_role_enum.create(op.get_bind(), checkfirst=True)

    platform_role_enum = postgresql.ENUM(
        "platform_operator",
        name="platform_role",
        create_type=False,
    )
    platform_role_enum.create(op.get_bind(), checkfirst=True)

    op.add_column("users", sa.Column("platform_role", platform_role_enum, nullable=True))

    op.alter_column(
        "tenant_user_memberships",
        "role",
        existing_type=sa.VARCHAR(length=32),
        type_=tenant_role_enum,
        nullable=False,
        postgresql_using="role::tenant_role",
    )
    op.alter_column(
        "tenant_member_invites",
        "role",
        existing_type=sa.VARCHAR(length=32),
        type_=tenant_role_enum,
        nullable=False,
        postgresql_using="role::tenant_role",
    )


def downgrade() -> None:
    tenant_role_enum = postgresql.ENUM(
        "viewer",
        "member",
        "admin",
        "owner",
        name="tenant_role",
        create_type=False,
    )
    platform_role_enum = postgresql.ENUM(
        "platform_operator",
        name="platform_role",
        create_type=False,
    )

    op.alter_column(
        "tenant_member_invites",
        "role",
        existing_type=tenant_role_enum,
        type_=sa.VARCHAR(length=32),
        nullable=False,
        postgresql_using="role::text",
    )
    op.alter_column(
        "tenant_user_memberships",
        "role",
        existing_type=tenant_role_enum,
        type_=sa.VARCHAR(length=32),
        nullable=False,
        postgresql_using="role::text",
    )

    op.drop_column("users", "platform_role")

    platform_role_enum.drop(op.get_bind(), checkfirst=True)
    tenant_role_enum.drop(op.get_bind(), checkfirst=True)
