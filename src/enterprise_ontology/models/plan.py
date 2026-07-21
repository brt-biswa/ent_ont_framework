"""Structured semantic plan — PRD Sec. 12. The LLM returns THIS, never SQL or prose."""
from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel, Field

from .enums import Operator, ComparisonBasis


class PlanFilter(BaseModel):
    dimension_id: str
    operator: Operator
    canonical_values: list[str] = Field(default_factory=list)


class SemanticPlan(BaseModel):
    """Mirrors the exact example schema in PRD Sec. 12."""
    plan_id: Optional[str] = None
    metric_ids: list[str] = Field(default_factory=list)
    dimension_ids: list[str] = Field(default_factory=list)
    filters: list[PlanFilter] = Field(default_factory=list)
    comparison: ComparisonBasis = ComparisonBasis.NONE
    time_period: Optional[str] = None
    sort: Optional[str] = None
    limit: int = Field(default=100, le=10_000)
    ontology_version: Optional[str] = None
    raw_question: Optional[str] = None


class PlanValidationResult(BaseModel):
    is_valid: bool
    plan: SemanticPlan
    violations: list[str] = Field(default_factory=list)
    requires_clarification: bool = False
    clarification_prompt: Optional[str] = None
    resolved_dimension_values: dict[str, Any] = Field(default_factory=dict)
