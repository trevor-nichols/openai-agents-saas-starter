"""enforce sso provider key format"""

revision = 'c44d51a2f265'
down_revision = 'a9b5b51c611e'
branch_labels = None
depends_on = None

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade() -> None:
    bind = op.get_bind()
    if bind is None or bind.dialect.name != "postgresql":
        return

    connection = bind

    duplicate_config = connection.execute(
        sa.text(
            """
            SELECT tenant_id, lower(provider_key) AS provider_key, COUNT(*) AS cnt
            FROM sso_provider_configs
            GROUP BY tenant_id, lower(provider_key)
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        )
    ).first()
    if duplicate_config is not None:
        raise RuntimeError(
            "Cannot enforce provider_key format: duplicate keys exist in sso_provider_configs "
            "when compared case-insensitively."
        )

    duplicate_identity_by_user = connection.execute(
        sa.text(
            """
            SELECT user_id, lower(provider_key) AS provider_key, COUNT(*) AS cnt
            FROM user_identities
            GROUP BY user_id, lower(provider_key)
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        )
    ).first()
    if duplicate_identity_by_user is not None:
        raise RuntimeError(
            "Cannot enforce provider_key format: duplicate keys exist in user_identities "
            "for the same user when compared case-insensitively."
        )

    duplicate_identity_by_subject = connection.execute(
        sa.text(
            """
            SELECT issuer, subject, lower(provider_key) AS provider_key, COUNT(*) AS cnt
            FROM user_identities
            GROUP BY issuer, subject, lower(provider_key)
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        )
    ).first()
    if duplicate_identity_by_subject is not None:
        raise RuntimeError(
            "Cannot enforce provider_key format: duplicate keys exist in user_identities "
            "for the same issuer/subject when compared case-insensitively."
        )

    invalid_config = connection.execute(
        sa.text(
            """
            SELECT provider_key
            FROM sso_provider_configs
            WHERE lower(provider_key) !~ '^[a-z0-9_]+$'
            LIMIT 1
            """
        )
    ).first()
    if invalid_config is not None:
        raise RuntimeError(
            "Cannot enforce provider_key format: invalid characters exist in "
            "sso_provider_configs (allowed: a-z, 0-9, underscore)."
        )

    invalid_identity = connection.execute(
        sa.text(
            """
            SELECT provider_key
            FROM user_identities
            WHERE lower(provider_key) !~ '^[a-z0-9_]+$'
            LIMIT 1
            """
        )
    ).first()
    if invalid_identity is not None:
        raise RuntimeError(
            "Cannot enforce provider_key format: invalid characters exist in "
            "user_identities (allowed: a-z, 0-9, underscore)."
        )

    op.execute("UPDATE sso_provider_configs SET provider_key = lower(provider_key)")
    op.execute("UPDATE user_identities SET provider_key = lower(provider_key)")

    op.create_check_constraint(
        "ck_sso_provider_configs_provider_key_lowercase",
        "sso_provider_configs",
        "provider_key = lower(provider_key)",
    )
    op.create_check_constraint(
        "ck_sso_provider_configs_provider_key_format",
        "sso_provider_configs",
        "provider_key ~ '^[a-z0-9_]+$'",
    )
    op.create_check_constraint(
        "ck_user_identities_provider_key_lowercase",
        "user_identities",
        "provider_key = lower(provider_key)",
    )
    op.create_check_constraint(
        "ck_user_identities_provider_key_format",
        "user_identities",
        "provider_key ~ '^[a-z0-9_]+$'",
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind is None or bind.dialect.name != "postgresql":
        return

    op.drop_constraint(
        "ck_user_identities_provider_key_format",
        "user_identities",
        type_="check",
    )
    op.drop_constraint(
        "ck_user_identities_provider_key_lowercase",
        "user_identities",
        type_="check",
    )
    op.drop_constraint(
        "ck_sso_provider_configs_provider_key_format",
        "sso_provider_configs",
        type_="check",
    )
    op.drop_constraint(
        "ck_sso_provider_configs_provider_key_lowercase",
        "sso_provider_configs",
        type_="check",
    )
