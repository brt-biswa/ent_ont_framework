"""ontology.metric_definition — PRD Sec. 6.3 metric layer."""
from __future__ import annotations
from typing import Optional
from pydantic import Field

from ._base import GovernedRecord
from .enums import TimeGrain


class MetricDefinition(GovernedRecord):
    metric_id: str = Field(..., description="e.g. METRIC.NET_REVENUE")
    concept_id: str
    business_definition: str
    formula: str = Field(..., description="Human-readable formula; execution comes from certified_source_asset")
    aggregation_behavior: str = Field(..., description="e.g. SUM, AVG, COUNT_DISTINCT, non-additive")
    allowed_dimension_ids: list[str] = Field(default_factory=list)
    prohibited_dimension_ids: list[str] = Field(default_factory=list)
    time_grain: TimeGrain = TimeGrain.MONTH
    currency: Optional[str] = None
    unit: Optional[str] = None
    comparison_rules: list[str] = Field(default_factory=list)
    materiality_threshold: Optional[float] = None
    certified_source_asset: str = Field(
        ..., description="Fully qualified metric view / UC function / trusted SQL asset"
    )
    is_certified: bool = False
