"""L2 Lakebase cache — PRD Sec. 19 "use for shared ontology projections, user
capability snapshots, short-lived resolution results, session state and
distributed coordination."

This module is a thin, typed convenience wrapper around
LakebaseStateRepository that (de)serializes OntologyContext to/from JSON and
attaches the ontology_version/policy_version every cache row must carry.
"""
from __future__ import annotations

import asyncio
import logging

from ..models import OntologyContext, UserContext
from ..repositories.lakebase_repository import LakebaseStateRepository

logger = logging.getLogger(__name__)


class L2LakebaseCache:
    def __init__(self, lakebase: LakebaseStateRepository):
        self._lakebase = lakebase

    async def get_user_projection(self, cache_key: str, user_context: UserContext) -> OntologyContext | None:
        row = await self._lakebase.get_user_projection(cache_key)
        if row is None:
            return None
        return OntologyContext.model_validate(row["projection"])

    async def put_user_projection(
        self, cache_key: str, user_context: UserContext, context: OntologyContext
    ) -> None:
        await self._lakebase.put_user_projection(
            cache_key=cache_key,
            principal_hash=user_context.entitlement_scope_hash(),
            projection=context.model_dump(mode="json"),
            ontology_version=context.ontology_version,
            policy_version=context.policy_version,
        )

    async def get_dimension_resolution(self, cache_key: str) -> dict | None:
        return await self._lakebase.get_dimension_resolution(cache_key)

    async def put_dimension_resolution(
        self, cache_key: str, dimension_id: str, user_context: UserContext,
        result: dict, confidence: float, ontology_version: str,
    ) -> None:
        await self._lakebase.put_dimension_resolution(
            cache_key=cache_key,
            dimension_id=dimension_id,
            principal_hash=user_context.entitlement_scope_hash(),
            result=result,
            confidence=confidence,
            ontology_version=ontology_version,
        )


async def _warm() -> None:
    """Pre-populate compiled_snapshot for each active domain's "core context"
    bundle so the first request of the day isn't a cold-cache miss. Scheduled
    by the `ontology_cache_warm` job in databricks.yml (every 15 min)."""
    from ..repositories.unity_catalog_repository import UnityCatalogOntologyRepository

    repo = UnityCatalogOntologyRepository()
    lakebase = LakebaseStateRepository()
    await lakebase.connect()
    try:
        rows = repo._query("SELECT DISTINCT domain FROM domain_registry")  # noqa: SLF001
        for row in rows:
            domain = row["domain"]
            concepts = await repo.resolve_terms(terms=[], domain=domain)
            snapshot_key = f"domain:{domain}:core_context"
            await lakebase.put_compiled_snapshot(
                snapshot_key=snapshot_key,
                payload={"domain": domain, "concept_count": len(concepts)},
                ontology_version=await repo._active_version(),  # noqa: SLF001
                policy_version=repo.settings.sql_policy_version,
            )
            logger.info("Warmed cache snapshot for domain=%s", domain)
    finally:
        await lakebase.close()


def warm_main() -> None:
    """Entry point registered in pyproject.toml as `run_cache_warm`."""
    asyncio.run(_warm())


if __name__ == "__main__":
    warm_main()
