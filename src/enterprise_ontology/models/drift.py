"""ontology.drift_event — PRD Sec. 23 drift detection."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

from .enums import DriftSeverity


class DriftEvent(BaseModel):
    drift_event_id: str
    concept_id: Optional[str] = None
    asset_mapping_id: Optional[str] = None
    drift_type: str = Field(
        ..., description="MISSING_TABLE|RENAMED_COLUMN|METRIC_DEF_CHANGE|FUNCTION_CHANGE|"
                          "HIERARCHY_CHANGE|NEW_CATEGORICAL_VALUE|DEPRECATED_SOURCE_IN_USE|"
                          "BROKEN_MAPPING|GENIE_CHANGE|TOOL_SCHEMA_CHANGE|SUPERSEDED_DOCUMENT|"
                          "CONFLICTING_DEFINITION|SECURITY_TAG_CHANGE|MISSING_OWNER",
    )
    severity: DriftSeverity
    description: str
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_blocking: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
