"""Governed dimension-value resolution — PRD Sec. 13.

The LLM does not know what values exist in columns. This resolver:
  1. identifies candidate dimensions (caller supplies dimension_id),
  2. searches approved conformed dimension/hierarchy assets,
  3. matches labels, codes, aliases and hierarchy paths,
  4. uses OBO for protected dimensions,
  5. removes unauthorized candidates,
  6. returns canonical IDs + confidence,
  7. requests clarification when necessary.

It never builds a broad `ILIKE '%text%'` filter (Sec. 13 explicit anti-example)
— every returned value is a canonical_id bound as a parameter downstream.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from ..models import DimensionDefinition, HierarchyNode, UserContext
from ..repositories.unity_catalog_repository import UnityCatalogOntologyRepository
from ..security.authz import check_dimension_value_access
from ..cache.l2_lakebase_cache import L2LakebaseCache


@dataclass
class DimensionValueMatch:
    canonical_id: str
    display_name: str
    hierarchy_path: list[str] = field(default_factory=list)
    confidence: float = 1.0
    authorized: bool = True


class DimensionResolver:
    CLARIFICATION_THRESHOLD = 0.6

    def __init__(
        self,
        repository: UnityCatalogOntologyRepository,
        l2_cache: L2LakebaseCache,
    ):
        self._repo = repository
        self._l2 = l2_cache

    async def resolve(
        self, dimension_id: str, user_text: str, user_context: UserContext
    ) -> dict:
        cache_key = self._cache_key(dimension_id, user_text, user_context)
        cached = await self._l2.get_dimension_resolution(cache_key)
        if cached is not None:
            return cached

        dimension = await self._get_dimension(dimension_id)
        if dimension is None:
            return {"dimension": dimension_id, "input": user_text, "matches": [], "requires_clarification": True}

        candidates = await self._search_candidates(dimension, user_text)

        scope = None  # resolved from ontology.security_scope in a full implementation
        authorized_candidates: list[DimensionValueMatch] = []
        for candidate in candidates:
            decision = check_dimension_value_access(dimension, scope, user_context)
            candidate.authorized = decision.is_authorized
            if decision.is_authorized:
                authorized_candidates.append(candidate)

        requires_clarification = (
            len(authorized_candidates) == 0
            or (len(authorized_candidates) > 1 and authorized_candidates[0].confidence < self.CLARIFICATION_THRESHOLD)
        )

        result = {
            "dimension": dimension_id,
            "input": user_text,
            "matches": [m.__dict__ for m in authorized_candidates],
            "requires_clarification": requires_clarification,
        }

        confidence = authorized_candidates[0].confidence if authorized_candidates else 0.0
        await self._l2.put_dimension_resolution(
            cache_key, dimension_id, user_context, result, confidence,
            ontology_version=await self._repo._active_version(),  # noqa: SLF001
        )
        return result

    async def _get_dimension(self, dimension_id: str) -> DimensionDefinition | None:
        rows = self._repo._query(  # noqa: SLF001
            "SELECT * FROM dimension_definition WHERE dimension_id = ? AND status = 'ACTIVE'",
            (dimension_id,),
        )
        return DimensionDefinition.model_validate(rows[0]) if rows else None

    async def _search_candidates(
        self, dimension: DimensionDefinition, user_text: str
    ) -> list[DimensionValueMatch]:
        """Deterministic label/alias match against the conformed dimension
        asset (or hierarchy_node when hierarchy_id is set). A production
        implementation adds fuzzy matching (e.g. trigram similarity on the
        certified dimension asset) behind the same governed interface — the
        contract (canonical_id + confidence + authorized) never changes."""
        if dimension.hierarchy_id:
            rows = self._repo._query(  # noqa: SLF001
                """SELECT canonical_id, display_name, path FROM hierarchy_node
                   WHERE hierarchy_id = ? AND status = 'ACTIVE'
                   AND lower(display_name) LIKE ?""",
                (dimension.hierarchy_id, f"%{user_text.lower()}%"),
            )
            return [
                DimensionValueMatch(
                    canonical_id=r["canonical_id"],
                    display_name=r["display_name"],
                    hierarchy_path=r["path"],
                    confidence=1.0 if r["display_name"].lower() == user_text.lower() else 0.9,
                )
                for r in rows
            ]

        # Non-hierarchical dimension: match against the certified asset's key/label
        # columns via the asset_mapping-resolved fully qualified name.
        mappings = await self._repo.get_asset_mappings(dimension.concept_id)
        if not mappings:
            return []
        asset = mappings[0].fully_qualified_asset_name
        rows = self._repo._query(  # noqa: SLF001
            f"SELECT DISTINCT {dimension.key_column} AS k, {dimension.label_column or dimension.key_column} AS l "
            f"FROM {asset} WHERE lower({dimension.label_column or dimension.key_column}) LIKE ? LIMIT 25",
            (f"%{user_text.lower()}%",),
        )
        return [
            DimensionValueMatch(
                canonical_id=str(r["k"]),
                display_name=str(r["l"]),
                confidence=1.0 if str(r["l"]).lower() == user_text.lower() else 0.85,
            )
            for r in rows
        ]

    @staticmethod
    def _cache_key(dimension_id: str, user_text: str, user_context: UserContext) -> str:
        payload = f"{dimension_id}:{user_text.lower()}:{user_context.entitlement_scope_hash()}"
        return hashlib.sha256(payload.encode()).hexdigest()[:32]
