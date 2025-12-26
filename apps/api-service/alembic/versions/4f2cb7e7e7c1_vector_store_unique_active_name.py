"""vector store unique active name"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "4f2cb7e7e7c1"
down_revision = "ed069381f12b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_vector_stores_tenant_name",
        "vector_stores",
        type_="unique",
    )
    op.create_index(
        "uq_vector_stores_tenant_name_active",
        "vector_stores",
        ["tenant_id", "name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
        sqlite_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_vector_stores_tenant_name_active", table_name="vector_stores")
    op.create_unique_constraint(
        "uq_vector_stores_tenant_name",
        "vector_stores",
        ["tenant_id", "name"],
    )
