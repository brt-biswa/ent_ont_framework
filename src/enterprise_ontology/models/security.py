"""ontology.security_scope / ontology.authority_source — PRD Sec. 6.7, 9."""
from __future__ import annotations
from typing import Optional
from pydantic import Field

from ._base import GovernedRecord
from .enums import Sensitivity, AuthorityLevel


class SecurityScope(GovernedRecord):
    scope_id: str
    concept_id: Optional[str] = None
    dimension_id: Optional[str] = None
    sensitivity: Sensitivity
    required_group: Optional[str] = Field(
        default=None, description="Account group required for RBAC grant check"
    )
    row_filter_expression: Optional[str] = None
    column_mask_expression: Optional[str] = None
    requires_obo: bool = False


class AuthoritySource(GovernedRecord):
    authority_source_id: str
    concept_id: str
    authority_level: AuthorityLevel
    source_reference: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    approved_by: Optional[str] = None
    review_date: Optional[str] = None
