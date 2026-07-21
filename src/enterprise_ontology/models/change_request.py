"""ontology.change_request / ontology.approval_history — PRD Sec. 22."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

from .enums import ChangeRequestStage


class ChangeRequest(BaseModel):
    change_request_id: str
    concept_id: Optional[str] = None
    business_reason: str
    old_definition: Optional[str] = None
    new_definition: str
    effective_date: str
    affected_metric_ids: list[str] = Field(default_factory=list)
    affected_dimension_ids: list[str] = Field(default_factory=list)
    affected_asset_mapping_ids: list[str] = Field(default_factory=list)
    affected_agent_ids: list[str] = Field(default_factory=list)
    affected_tool_ids: list[str] = Field(default_factory=list)
    affected_test_question_ids: list[str] = Field(default_factory=list)
    migration_plan: Optional[str] = None
    stage: ChangeRequestStage = ChangeRequestStage.SUBMITTED
    submitted_by: str
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApprovalHistory(BaseModel):
    approval_id: str
    change_request_id: str
    stage: ChangeRequestStage
    approver: str
    decision: str = Field(..., description="APPROVED | REJECTED | CHANGES_REQUESTED")
    comment: Optional[str] = None
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
