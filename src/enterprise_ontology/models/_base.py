"""Shared base model with the governance fields every ontology row must carry."""
from __future__ import annotations
from datetime import datetime, date, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from .enums import LifecycleStatus, Sensitivity, Discoverability


class GovernedRecord(BaseModel):
    """Every ontology registry row is versioned, effective-dated, owned and
    security-classified (PRD Sec. 6.1, design principles 4, 13, 15)."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    owner: str
    steward: Optional[str] = None
    status: LifecycleStatus = LifecycleStatus.DRAFT
    sensitivity: Sensitivity = Sensitivity.INTERNAL
    discoverability: Discoverability = Discoverability.REQUEST_ACCESS
    effective_from: date
    effective_to: Optional[date] = None
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = None

    def is_active_on(self, as_of: date) -> bool:
        if self.status != LifecycleStatus.ACTIVE:
            return False
        if as_of < self.effective_from:
            return False
        if self.effective_to is not None and as_of > self.effective_to:
            return False
        return True
