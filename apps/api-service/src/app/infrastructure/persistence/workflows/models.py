from __future__ import annotations

from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

from app.infrastructure.persistence.models.base import Base as ModelBase


class WorkflowRunModel(ModelBase):
    __tablename__ = "workflow_runs"

    id = Column(String, primary_key=True)
    workflow_key = Column(String, nullable=False, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    final_output_text = Column(String, nullable=True)
    final_output_structured = Column(JSONB if JSONB is not None else JSON, nullable=True)
    trace_id = Column(String, nullable=True)
    request_message = Column(String, nullable=True)
    conversation_id = Column(String, nullable=True)
    metadata_json = Column("metadata", JSONB if JSONB is not None else JSON, nullable=True)


class WorkflowRunStepModel(ModelBase):
    __tablename__ = "workflow_run_steps"

    id = Column(String, primary_key=True)
    workflow_run_id = Column(String, nullable=False, index=True)
    sequence_no = Column(Integer, nullable=False)
    step_name = Column(String, nullable=False)
    step_agent = Column(String, nullable=False)
    status = Column(String, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    response_id = Column(String, nullable=True)
    response_text = Column(String, nullable=True)
    structured_output = Column(JSONB if JSONB is not None else JSON, nullable=True)
    raw_payload = Column(JSONB if JSONB is not None else JSON, nullable=True)
    usage_input_tokens = Column(Integer, nullable=True)
    usage_output_tokens = Column(Integer, nullable=True)
    stage_name = Column(String, nullable=True)
    parallel_group = Column(String, nullable=True)
    branch_index = Column(Integer, nullable=True)
