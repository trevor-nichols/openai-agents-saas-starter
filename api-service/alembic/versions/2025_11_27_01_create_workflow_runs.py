"""create workflow runs tables

Revision ID: 20251127_010000
Revises: 20251126_130200
Create Date: 2025-11-27
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20251127_010000"
down_revision: Union[str, None] = "20251126_130200"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("workflow_key", sa.String(), nullable=False, index=True),
        sa.Column("tenant_id", sa.String(), nullable=False, index=True),
        sa.Column("user_id", sa.String(), nullable=False, index=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("final_output_text", sa.String(), nullable=True),
        sa.Column(
            "final_output_structured",
            sa.JSON().with_variant(sa.dialects.postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
        sa.Column("trace_id", sa.String(), nullable=True),
        sa.Column("request_message", sa.String(), nullable=True),
        sa.Column("conversation_id", sa.String(), nullable=True),
        sa.Column(
            "metadata",
            sa.JSON().with_variant(sa.dialects.postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
    )

    op.create_table(
        "workflow_run_steps",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("workflow_run_id", sa.String(), nullable=False, index=True),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("step_name", sa.String(), nullable=False),
        sa.Column("step_agent", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_id", sa.String(), nullable=True),
        sa.Column("response_text", sa.String(), nullable=True),
        sa.Column(
            "structured_output",
            sa.JSON().with_variant(sa.dialects.postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
        sa.Column(
            "raw_payload",
            sa.JSON().with_variant(sa.dialects.postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
        sa.Column("usage_input_tokens", sa.Integer(), nullable=True),
        sa.Column("usage_output_tokens", sa.Integer(), nullable=True),
    )

    op.create_index(
        "ix_workflow_run_steps_run_seq",
        "workflow_run_steps",
        ["workflow_run_id", "sequence_no"],
    )


def downgrade() -> None:
    op.drop_index("ix_workflow_run_steps_run_seq", table_name="workflow_run_steps")
    op.drop_table("workflow_run_steps")
    op.drop_table("workflow_runs")
