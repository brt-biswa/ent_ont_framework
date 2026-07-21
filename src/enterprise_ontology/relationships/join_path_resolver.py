"""Approved join-path resolution — PRD Sec. 6.2, 10: "the LLM must never
invent joins." Backs the `get_approved_join_path` MCP tool.
"""
from __future__ import annotations

from ..repositories.unity_catalog_repository import UnityCatalogOntologyRepository


class JoinPathResolver:
    def __init__(self, repository: UnityCatalogOntologyRepository):
        self._repo = repository

    async def get_join_path(self, source_concept_id: str, target_concept_id: str) -> str | None:
        direct = await self._repo.get_approved_join_path(source_concept_id, target_concept_id)
        if direct:
            return direct
        # Try the reverse direction — a relationship recorded A->B is usable
        # for a B->A traversal as long as cardinality allows it; a fuller
        # implementation would inspect cardinality here before accepting it.
        return await self._repo.get_approved_join_path(target_concept_id, source_concept_id)

    async def get_join_path_chain(self, concept_ids: list[str]) -> list[str]:
        """Resolve a chain of joins for >2 concepts, e.g. [Customer, Order,
        Order Line]. Returns an ordered list of join expressions, or raises
        if any hop lacks an approved relationship — the compiler must never
        fall back to guessing a join for the missing hop."""
        joins: list[str] = []
        for a, b in zip(concept_ids, concept_ids[1:]):
            join = await self.get_join_path(a, b)
            if join is None:
                raise ValueError(f"No approved join path between {a} and {b} — refusing to guess")
            joins.append(join)
        return joins
