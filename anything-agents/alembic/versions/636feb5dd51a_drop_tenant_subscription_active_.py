"""Drop tenant subscription unique constraint relying on deferrable semantics."""

from __future__ import annotations

from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "636feb5dd51a"
down_revision = "6724700351b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":  # pragma: no cover - sqlite cannot drop constraints easily
        return

    inspector = inspect(bind)
    existing_constraints = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("tenant_subscriptions")
    }
    if "uq_tenant_subscriptions_active" in existing_constraints:
        op.drop_constraint(
            "uq_tenant_subscriptions_active",
            "tenant_subscriptions",
            type_="unique",
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":  # pragma: no cover - skip for sqlite
        return

    op.create_unique_constraint(
        "uq_tenant_subscriptions_active",
        "tenant_subscriptions",
        ["tenant_id", "status"],
    )
