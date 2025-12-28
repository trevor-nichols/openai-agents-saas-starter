"""Add billing customers table."""

revision = "e8a40a39b480"
down_revision = "4f2cb7e7e7c1"
branch_labels = None
depends_on = None

from alembic import op  # noqa: E402
import sqlalchemy as sa  # noqa: E402


def upgrade() -> None:
    op.create_table(
        "billing_customers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("processor", sa.String(length=32), nullable=False),
        sa.Column("processor_customer_id", sa.String(length=128), nullable=False),
        sa.Column("billing_email", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant_accounts.id"],
            name=op.f("fk_billing_customers_tenant_id_tenant_accounts"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_billing_customers")),
        sa.UniqueConstraint(
            "tenant_id",
            "processor",
            name="uq_billing_customers_tenant_processor",
        ),
    )
    op.create_index(
        "ix_billing_customers_processor_customer_id",
        "billing_customers",
        ["processor_customer_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_billing_customers_processor_customer_id",
        table_name="billing_customers",
    )
    op.drop_table("billing_customers")
