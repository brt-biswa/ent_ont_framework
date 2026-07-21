"""ontology.relationship — PRD Sec. 6.2 relationship layer."""
from __future__ import annotations
from typing import Optional
from pydantic import Field

from ._base import GovernedRecord


class Relationship(GovernedRecord):
    relationship_id: str
    source_concept_id: str
    predicate: str
    target_concept_id: str
    cardinality: str = Field(..., description="e.g. ONE_TO_MANY, MANY_TO_MANY")
    required: bool = False
    approved_join_ref: Optional[str] = Field(
        default=None, description="Fully qualified join key reference, resolved by join_path_resolver"
    )
    security_implications: Optional[str] = None
