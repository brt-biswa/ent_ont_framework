"""ontology.concept — PRD Sec. 6.1 business concept layer."""
from __future__ import annotations
from typing import Optional
from pydantic import Field

from ._base import GovernedRecord
from .enums import ConceptType, AuthorityLevel


class Concept(GovernedRecord):
    concept_id: str = Field(..., description="Stable canonical ID, e.g. METRIC.NET_REVENUE")
    canonical_name: str
    concept_type: ConceptType
    definition: str
    domain: str
    subdomain: Optional[str] = None
    authority_level: AuthorityLevel = AuthorityLevel.APPROVED_GLOSSARY
    examples: list[str] = Field(default_factory=list)
    non_examples: list[str] = Field(default_factory=list)
