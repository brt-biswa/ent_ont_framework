"""ontology.version — PRD Sec. 22 versioning and lifecycle."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class OntologyVersion(BaseModel):
    version_id: str
    label: str = Field(..., description="e.g. 2026.07.1")
    is_active: bool = False
    activated_at: Optional[datetime] = None
    activated_by: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
