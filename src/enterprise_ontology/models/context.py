"""User / execution context and the permission-aware ontology context projection.

Design principle 11 (PRD Sec. 5): OBO is used for user-specific protected access.
Design principle 19: authorization failures fail closed.
Never persist an OAuth token on these models — see security/obo.py.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field

from .concept import Concept
from .metric import MetricDefinition
from .dimension import DimensionDefinition
from .relationship import Relationship
from .business_rule import BusinessRule


class UserContext(BaseModel):
    """Identity must come from trusted auth context, never a client-supplied payload
    (PRD Sec. 19, cache-key requirements)."""

    principal_id: str
    display_name: Optional[str] = None
    entitlement_group_ids: list[str] = Field(default_factory=list)
    is_service_principal: bool = False
    obo_token_present: bool = Field(
        default=False,
        description="Flag only — the token itself is never stored on this model or persisted.",
    )
    environment: str = "dev"

    def entitlement_scope_hash(self) -> str:
        """Stable hash used as part of cache keys (PRD Sec. 19) — never the raw token."""
        import hashlib
        payload = f"{self.principal_id}:{sorted(self.entitlement_group_ids)}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


class OntologyContext(BaseModel):
    """A small, relevant, permission-aware ontology projection — never the full
    ontology (PRD Sec. 12)."""

    ontology_version: str
    policy_version: str
    matched_concepts: list[Concept] = Field(default_factory=list)
    approved_metrics: list[MetricDefinition] = Field(default_factory=list)
    approved_dimensions: list[DimensionDefinition] = Field(default_factory=list)
    relevant_relationships: list[Relationship] = Field(default_factory=list)
    business_rules: list[BusinessRule] = Field(default_factory=list)
    approved_sources: list[str] = Field(default_factory=list)
    security_constraints: list[str] = Field(default_factory=list)
