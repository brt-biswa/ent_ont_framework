"""ontology.dimension_definition — PRD Sec. 6.3 dimension layer."""
from __future__ import annotations
from typing import Optional
from pydantic import Field

from ._base import GovernedRecord
from .enums import Operator, ValueResolutionStrategy


class DimensionDefinition(GovernedRecord):
    dimension_id: str = Field(..., description="e.g. ORG.OPERATING_UNIT")
    concept_id: str
    key_column: str
    label_column: Optional[str] = None
    hierarchy_id: Optional[str] = None
    allowed_operators: list[Operator] = Field(default_factory=lambda: [Operator.EQUALS, Operator.IN])
    value_resolution_strategy: ValueResolutionStrategy = ValueResolutionStrategy.EXACT_MATCH
    high_cardinality: bool = False
    requires_obo: bool = False
