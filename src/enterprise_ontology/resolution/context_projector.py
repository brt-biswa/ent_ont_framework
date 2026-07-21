"""Builds the small, permission-aware ontology projection the LLM actually
sees (PRD Sec. 12). Never the full ontology — only matched concepts, their
approved metrics/dimensions, relevant relationships, applicable business
rules, approved sources and security constraints, filtered by the caller's
UserContext.

This is where the L1/L2 caches (cache/) are consulted before hitting Unity
Catalog, and where drift status (via LakebaseStateRepository) is checked so a
concept currently blocked by CRITICAL drift is dropped from the projection
rather than silently served (PRD Sec. 23: "critical drift must block
production use").
"""
from __future__ import annotations

import logging

from ..models import OntologyContext, UserContext
from ..repositories.unity_catalog_repository import UnityCatalogOntologyRepository
from ..repositories.lakebase_repository import LakebaseStateRepository
from ..cache.l1_memory_cache import L1MemoryCache
from ..cache.l2_lakebase_cache import L2LakebaseCache

logger = logging.getLogger(__name__)


class ContextProjector:
    def __init__(
        self,
        repository: UnityCatalogOntologyRepository,
        lakebase: LakebaseStateRepository,
        l1_cache: L1MemoryCache | None = None,
        l2_cache: L2LakebaseCache | None = None,
    ):
        self._repo = repository
        self._lakebase = lakebase
        self._l1 = l1_cache or L1MemoryCache()
        self._l2 = l2_cache or L2LakebaseCache(lakebase)

    async def project(self, concept_ids: list[str], user_context: UserContext) -> OntologyContext:
        if not concept_ids:
            return await self._repo.get_context([], user_context)

        cache_key = self._cache_key(concept_ids, user_context)

        cached = self._l1.get(cache_key)
        if cached is not None:
            return await self._drop_blocked_concepts(cached, user_context)

        cached = await self._l2.get_user_projection(cache_key, user_context)
        if cached is not None:
            self._l1.set(cache_key, cached)
            return await self._drop_blocked_concepts(cached, user_context)

        context = await self._repo.get_context(concept_ids, user_context)
        self._l1.set(cache_key, context)
        await self._l2.put_user_projection(cache_key, user_context, context)
        return await self._drop_blocked_concepts(context, user_context)

    async def _drop_blocked_concepts(
        self, context: OntologyContext, user_context: UserContext
    ) -> OntologyContext:
        blocked = set(await self._lakebase.get_blocking_concepts())
        if not blocked:
            return context
        filtered = context.model_copy(
            update={
                "matched_concepts": [c for c in context.matched_concepts if c.concept_id not in blocked],
                "approved_metrics": [m for m in context.approved_metrics if m.concept_id not in blocked],
                "approved_dimensions": [d for d in context.approved_dimensions if d.concept_id not in blocked],
            }
        )
        if len(filtered.matched_concepts) != len(context.matched_concepts):
            logger.warning("Dropped %d concept(s) blocked by critical drift", len(blocked))
        return filtered

    @staticmethod
    def _cache_key(concept_ids: list[str], user_context: UserContext) -> str:
        # environment + entitlement-scope hash + sorted concept ids, per the
        # cache-key composition required by PRD Sec. 19.
        joined = ",".join(sorted(concept_ids))
        return f"{user_context.environment}:{user_context.entitlement_scope_hash()}:{joined}"
