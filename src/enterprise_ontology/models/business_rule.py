"""ontology.business_rule — PRD Sec. 6.4 business rules and constraints."""
from __future__ import annotations
from typing import Optional
from pydantic import Field

from ._base import GovernedRecord
from .enums import RuleType


class BusinessRule(GovernedRecord):
    rule_id: str
    concept_id: str
    rule_type: RuleType
    description: str
    executable_reference: Optional[str] = Field(
        default=None,
        description="Metric view / certified view / UC function / DQ rule implementing this — "
                    "critical rules MUST NOT exist only in prompts (Sec. 6.4)",
    )
