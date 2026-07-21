"""Certified metric service — PRD Sec. 10 "metric management". Backs the
`resolve_metric` and `get_metric_definition` MCP tools. Validates dimension
compatibility so the planner/validator never has to duplicate this logic.
"""
from __future__ import annotations

from ..models import MetricDefinition
from ..repositories.unity_catalog_repository import UnityCatalogOntologyRepository


class MetricService:
    def __init__(self, repository: UnityCatalogOntologyRepository):
        self._repo = repository

    async def get(self, metric_id: str) -> MetricDefinition | None:
        rows = self._repo._query(  # noqa: SLF001
            "SELECT * FROM metric_definition WHERE metric_id = ? AND status = 'ACTIVE'", (metric_id,)
        )
        return MetricDefinition.model_validate(rows[0]) if rows else None

    async def is_dimension_compatible(self, metric_id: str, dimension_id: str) -> tuple[bool, str]:
        metric = await self.get(metric_id)
        if metric is None:
            return False, f"Unknown or uncertified metric {metric_id}"
        if dimension_id in metric.prohibited_dimension_ids:
            return False, f"{dimension_id} is explicitly prohibited for {metric_id}"
        if metric.allowed_dimension_ids and dimension_id not in metric.allowed_dimension_ids:
            return False, f"{dimension_id} is not in the allowed-dimension list for {metric_id}"
        return True, "compatible"

    async def resolve_by_term(self, term: str, domain: str | None = None) -> list[MetricDefinition]:
        concepts = await self._repo.resolve_terms([term], domain=domain)
        results: list[MetricDefinition] = []
        for concept in concepts:
            rows = self._repo._query(  # noqa: SLF001
                "SELECT * FROM metric_definition WHERE concept_id = ? AND status = 'ACTIVE'",
                (concept.concept_id,),
            )
            results.extend(MetricDefinition.model_validate(r) for r in rows)
        return results
