"""Ensure single agent→vector store binding per tenant."""

revision = 'fd0d6a8ba881'
down_revision = '20251203_120000'
branch_labels = None
depends_on = None

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind else "postgresql"

    if dialect == "sqlite":
        op.execute(
            """
            DELETE FROM agent_vector_stores
            WHERE rowid NOT IN (
                SELECT MIN(rowid)
                FROM agent_vector_stores
                GROUP BY tenant_id, agent_key
            )
            """
        )
    else:
        op.execute(
            """
            DELETE FROM agent_vector_stores a
            USING (
                SELECT MIN(ctid) AS ctid, tenant_id, agent_key
                FROM agent_vector_stores
                GROUP BY tenant_id, agent_key
            ) keep
            WHERE a.tenant_id = keep.tenant_id
              AND a.agent_key = keep.agent_key
              AND a.ctid <> keep.ctid
            """
        )

    op.create_unique_constraint(
        "uq_agent_vector_store_per_agent",
        "agent_vector_stores",
        ["tenant_id", "agent_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_agent_vector_store_per_agent", "agent_vector_stores", type_="unique"
    )
