"""Business rule lookup — PRD Sec. 10 "business-rule management". Backs the
`get_business_rule` MCP tool and feeds business_rules into the ontology
context projection so the planner/validator can enforce rules that have an
executable_reference (e.g. an eligibility UC function) rather than guessing.
"""
from __future__ import annotations

from ..models import BusinessRule
from ..repositories.unity_catalog_repository import UnityCatalogOntologyRepository


class RuleService:
    def __init__(self, repository: UnityCatalogOntologyRepository):
        self._repo = repository

    async def get_rules_for_concept(self, concept_id: str) -> list[BusinessRule]:
        rows = self._repo._query(  # noqa: SLF001
            "SELECT * FROM business_rule WHERE concept_id = ? AND status = 'ACTIVE'", (concept_id,)
        )
        return [BusinessRule.model_validate(r) for r in rows]

    async def get_rule(self, rule_id: str) -> BusinessRule | None:
        rows = self._repo._query(  # noqa: SLF001
            "SELECT * FROM business_rule WHERE rule_id = ? AND status = 'ACTIVE'", (rule_id,)
        )
        return BusinessRule.model_validate(rows[0]) if rows else None
