"""Unity Catalog-backed implementation of OntologyRepositoryProtocol.

Reads the `ontology.*` Delta tables (see sql/unity_catalog/) through a
Databricks SQL warehouse. This repository is READ-mostly at runtime: writes
happen through the change-request workflow (governance/admin UI), not through
agent-facing calls, per design principle 12 ("new ontology elements require
review and approval").

Permission-aware projection (design principle 6): callers pass a UserContext
and only concepts/metrics/dimensions the caller's entitlement groups can see
are ever returned. RBAC/ABAC in Unity Catalog remains the final boundary
(design principle 10) — this layer adds an ontology-level discoverability
filter on top, it does not replace UC grants.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any, Optional

from databricks import sql as databricks_sql

from ..config import Settings, get_settings
from ..models import (
    Concept, MetricDefinition, DimensionDefinition, Relationship, BusinessRule,
    AssetMapping, Synonym, OntologyContext, UserContext, Discoverability,
)

logger = logging.getLogger(__name__)


class UnityCatalogOntologyRepository:
    """Thin, connection-pooled data-access layer over the `ontology` UC schema."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._catalog = self.settings.ontology_catalog

    # -- low level -----------------------------------------------------
    def _connect(self):
        return databricks_sql.connect(
            server_hostname=self.settings.databricks_host,
            http_path=self.settings.warehouse_http_path,
            access_token=self.settings.databricks_token,
            catalog=self._catalog,
            schema="ontology",
        )

    def _query(self, sql_text: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_text, params)
                columns = [c[0] for c in cur.description]
                return [dict(zip(columns, row)) for row in cur.fetchall()]

    # -- concept / synonym resolution -----------------------------------
    async def resolve_terms(self, terms: list[str], domain: str | None = None) -> list[Concept]:
        """Exact + synonym lookup (PRD Sec. 10 "ontology retrieval"). Semantic
        (embedding) lookup is layered on top by resolution/concept_resolver.py —
        this method only does the deterministic, governed part."""
        placeholders = ",".join(["?"] * len(terms))
        domain_clause = "AND c.domain = ?" if domain else ""
        sql_text = f"""
            SELECT DISTINCT c.*
            FROM concept c
            LEFT JOIN synonym s ON s.concept_id = c.concept_id AND s.status = 'ACTIVE'
            WHERE (
                lower(c.canonical_name) IN ({placeholders})
                OR lower(s.term) IN ({placeholders})
            )
            AND c.status = 'ACTIVE'
            AND s.synonym_type != 'PROHIBITED_EQUIVALENCE'
            {domain_clause}
        """
        lowered = [t.lower() for t in terms]
        params: tuple[Any, ...] = tuple(lowered) + tuple(lowered)
        if domain:
            params = params + (domain,)
        rows = self._query(sql_text, params)
        return [Concept.model_validate(r) for r in rows]

    # -- permission-aware context projection -----------------------------
    async def get_context(self, concept_ids: list[str], user_context: UserContext) -> OntologyContext:
        if not concept_ids:
            return OntologyContext(
                ontology_version=await self._active_version(),
                policy_version=self.settings.sql_policy_version,
            )

        placeholders = ",".join(["?"] * len(concept_ids))

        concepts = [
            Concept.model_validate(r)
            for r in self._query(
                f"SELECT * FROM concept WHERE concept_id IN ({placeholders}) AND status='ACTIVE'",
                tuple(concept_ids),
            )
            if self._is_discoverable(r, user_context)
        ]
        metrics = [
            MetricDefinition.model_validate(r)
            for r in self._query(
                f"SELECT * FROM metric_definition WHERE concept_id IN ({placeholders}) AND status='ACTIVE'",
                tuple(concept_ids),
            )
            if self._is_discoverable(r, user_context)
        ]
        dimensions = [
            DimensionDefinition.model_validate(r)
            for r in self._query(
                f"SELECT * FROM dimension_definition WHERE concept_id IN ({placeholders}) AND status='ACTIVE'",
                tuple(concept_ids),
            )
            if self._is_discoverable(r, user_context)
        ]
        relationships = [
            Relationship.model_validate(r)
            for r in self._query(
                f"""SELECT * FROM relationship
                    WHERE (source_concept_id IN ({placeholders}) OR target_concept_id IN ({placeholders}))
                    AND status='ACTIVE'""",
                tuple(concept_ids) + tuple(concept_ids),
            )
        ]
        rules = [
            BusinessRule.model_validate(r)
            for r in self._query(
                f"SELECT * FROM business_rule WHERE concept_id IN ({placeholders}) AND status='ACTIVE'",
                tuple(concept_ids),
            )
        ]
        sources = [
            r["fully_qualified_asset_name"]
            for r in self._query(
                f"SELECT DISTINCT fully_qualified_asset_name FROM asset_mapping "
                f"WHERE concept_id IN ({placeholders}) AND is_certified = true AND status='ACTIVE'",
                tuple(concept_ids),
            )
        ]

        return OntologyContext(
            ontology_version=await self._active_version(),
            policy_version=self.settings.sql_policy_version,
            matched_concepts=concepts,
            approved_metrics=metrics,
            approved_dimensions=dimensions,
            relevant_relationships=relationships,
            business_rules=rules,
            approved_sources=sources,
            security_constraints=[
                f"sensitivity={c.sensitivity.value}" for c in concepts if c.sensitivity.value != "PUBLIC"
            ],
        )

    async def get_approved_join_path(self, source_concept_id: str, target_concept_id: str) -> Optional[str]:
        rows = self._query(
            """SELECT approved_join_ref FROM relationship
               WHERE source_concept_id = ? AND target_concept_id = ? AND status = 'ACTIVE'
               AND approved_join_ref IS NOT NULL LIMIT 1""",
            (source_concept_id, target_concept_id),
        )
        return rows[0]["approved_join_ref"] if rows else None

    async def get_asset_mappings(self, concept_id: str) -> list[AssetMapping]:
        rows = self._query(
            "SELECT * FROM asset_mapping WHERE concept_id = ? AND status = 'ACTIVE'",
            (concept_id,),
        )
        return [AssetMapping.model_validate(r) for r in rows]

    async def _active_version(self) -> str:
        rows = self._query("SELECT label FROM version WHERE is_active = true LIMIT 1")
        return rows[0]["label"] if rows else "UNKNOWN"

    @staticmethod
    def _is_discoverable(row: dict[str, Any], user_context: UserContext) -> bool:
        """Ontology-level discoverability check (defense in depth on top of UC RBAC/ABAC).
        Fails closed: HIDDEN or unresolvable discoverability -> not returned unless the
        caller's entitlement groups explicitly include the required group."""
        disc = row.get("discoverability", Discoverability.REQUEST_ACCESS.value)
        if disc == Discoverability.OPEN.value:
            return True
        if disc == Discoverability.HIDDEN.value:
            return False
        required_group = row.get("required_group")
        if required_group is None:
            return True
        return required_group in user_context.entitlement_group_ids
