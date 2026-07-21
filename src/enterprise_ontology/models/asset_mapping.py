"""ontology.asset_mapping — PRD Sec. 6.6 physical asset mapping layer."""
from __future__ import annotations
from typing import Optional
from pydantic import Field

from ._base import GovernedRecord
from .enums import AssetType


class AssetMapping(GovernedRecord):
    mapping_id: str
    concept_id: str
    asset_type: AssetType
    fully_qualified_asset_name: str
    field_measure_or_function: Optional[str] = None
    mapping_expression: Optional[str] = None
    approved_join: Optional[str] = None
    source_system: Optional[str] = None
    freshness_sla_minutes: Optional[int] = None
    is_certified: bool = False
    data_quality_state: str = "UNKNOWN"
