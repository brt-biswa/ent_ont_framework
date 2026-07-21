"""Request/response schemas for the REST API — PRD Sec. 20 endpoint list."""
from __future__ import annotations

from pydantic import BaseModel

from ..models import SemanticPlan


class ResolveRequest(BaseModel):
    terms: list[str]
    domain: str | None = None


class ResolveDimensionRequest(BaseModel):
    dimension_id: str
    user_text: str


class ResolveHierarchyRequest(BaseModel):
    hierarchy_id: str
    canonical_id: str
    include_self: bool = True


class JoinPathRequest(BaseModel):
    source_concept_id: str
    target_concept_id: str


class ValidatePlanRequest(BaseModel):
    plan: SemanticPlan


class ChangeRequestCreate(BaseModel):
    concept_id: str | None = None
    business_reason: str
    old_definition: str | None = None
    new_definition: str
    effective_date: str
    migration_plan: str | None = None
