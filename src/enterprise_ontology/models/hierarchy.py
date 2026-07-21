"""ontology.hierarchy / ontology.hierarchy_node — PRD Sec. 6.3, 13 hierarchy resolution."""
from __future__ import annotations
from typing import Optional
from pydantic import Field

from ._base import GovernedRecord


class Hierarchy(GovernedRecord):
    hierarchy_id: str
    concept_id: str
    name: str
    max_depth: Optional[int] = None


class HierarchyNode(GovernedRecord):
    node_id: str
    hierarchy_id: str
    parent_node_id: Optional[str] = None
    canonical_id: str = Field(..., description="e.g. SH-EMEA-ENTERPRISE")
    display_name: str
    path: list[str] = Field(default_factory=list, description="Full path from root, e.g. ['Global Sales','EMEA','Enterprise']")
    level: int = 0
