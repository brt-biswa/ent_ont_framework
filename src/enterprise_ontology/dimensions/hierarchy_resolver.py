"""Hierarchy node resolution and expansion — backs the `resolve_hierarchy_node`
and `expand_hierarchy` MCP tools (PRD Sec. 11).

Because ontology.hierarchy_node stores the full materialized path per node
(sql/unity_catalog/016_ontology_hierarchy_node.sql), expansion is a single
filtered scan rather than a recursive CTE at request time — this matters for
the P95 < 1s dimension-resolution latency target (PRD Sec. 26).
"""
from __future__ import annotations

from ..models import HierarchyNode
from ..repositories.unity_catalog_repository import UnityCatalogOntologyRepository


class HierarchyResolver:
    def __init__(self, repository: UnityCatalogOntologyRepository):
        self._repo = repository

    async def resolve_node(self, hierarchy_id: str, canonical_id: str) -> HierarchyNode | None:
        rows = self._repo._query(  # noqa: SLF001
            "SELECT * FROM hierarchy_node WHERE hierarchy_id = ? AND canonical_id = ? AND status = 'ACTIVE'",
            (hierarchy_id, canonical_id),
        )
        return HierarchyNode.model_validate(rows[0]) if rows else None

    async def expand(self, hierarchy_id: str, canonical_id: str, include_self: bool = True) -> list[HierarchyNode]:
        """Return every descendant of the given node (all nodes whose path
        starts with this node's path) — used e.g. to expand "EMEA" into every
        leaf operating unit under it for a rollup query."""
        node = await self.resolve_node(hierarchy_id, canonical_id)
        if node is None:
            return []

        prefix = node.path
        rows = self._repo._query(  # noqa: SLF001
            "SELECT * FROM hierarchy_node WHERE hierarchy_id = ? AND status = 'ACTIVE'",
            (hierarchy_id,),
        )
        descendants = [
            HierarchyNode.model_validate(r)
            for r in rows
            if r["path"][: len(prefix)] == prefix and (include_self or r["path"] != prefix)
        ]
        return descendants

    async def ancestors(self, hierarchy_id: str, canonical_id: str) -> list[str]:
        node = await self.resolve_node(hierarchy_id, canonical_id)
        return node.path[:-1] if node else []
