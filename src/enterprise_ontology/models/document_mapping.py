"""ontology.document_mapping — PRD Sec. 18 AI Search integration chunk metadata."""
from __future__ import annotations
from typing import Optional
from pydantic import Field

from ._base import GovernedRecord


class DocumentMapping(GovernedRecord):
    document_mapping_id: str
    concept_ids: list[str] = Field(default_factory=list)
    document_id: str
    title: str
    section: Optional[str] = None
    page: Optional[int] = None
    jurisdiction: Optional[str] = None
    domain: Optional[str] = None
    approval_state: str = "DRAFT"
    superseded_by_document_id: Optional[str] = None
    source_uri: Optional[str] = None
