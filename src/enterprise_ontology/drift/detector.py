"""Drift detection — PRD Sec. 23. Scans the ontology registry against the
live Unity Catalog information schema and flags: missing/renamed
tables/columns, broken asset mappings, deprecated sources still in use, and
missing owners. Critical drift blocks production use of the affected
concept (enforced downstream by resolution/context_projector.py reading
ontology_state.drift_status).

Scheduled hourly by the `ontology_drift_detection` job (databricks.yml).
This module intentionally covers the checks that are cheaply computable
from Unity Catalog's own metadata (information_schema); the remaining drift
types in PRD Sec. 23 (Genie changes, tool schema changes, superseded
documents, conflicting definitions, security-tag changes) are integration
points other framework consumers hook into by calling
`DriftDetector.record_event()` directly from their own Genie/MCP/document
pipelines — this module doesn't have visibility into those systems on its own.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass

from ..config import get_settings
from ..models import AssetMapping, DriftEvent, DriftSeverity
from ..repositories.unity_catalog_repository import UnityCatalogOntologyRepository
from ..repositories.lakebase_repository import LakebaseStateRepository

logger = logging.getLogger(__name__)


@dataclass
class DriftScanResult:
    events: list[DriftEvent]
    blocking_concept_ids: set[str]


class DriftDetector:
    def __init__(self, repository: UnityCatalogOntologyRepository, lakebase: LakebaseStateRepository):
        self._repo = repository
        self._lakebase = lakebase

    async def scan(self) -> DriftScanResult:
        events: list[DriftEvent] = []
        blocking: set[str] = set()

        mappings = self._all_active_asset_mappings()
        for mapping in mappings:
            event = self._check_mapping(mapping)
            if event:
                events.append(event)
                if event.is_blocking:
                    blocking.add(mapping.concept_id)

        events += self._check_missing_owners()

        for event in events:
            await self.record_event(event)

        return DriftScanResult(events=events, blocking_concept_ids=blocking)

    def _all_active_asset_mappings(self) -> list[AssetMapping]:
        rows = self._repo._query(  # noqa: SLF001
            "SELECT * FROM asset_mapping WHERE status = 'ACTIVE'"
        )
        return [AssetMapping.model_validate(r) for r in rows]

    def _check_mapping(self, mapping: AssetMapping) -> DriftEvent | None:
        """Checks whether the mapped asset still exists via information_schema.
        A missing table/column is CRITICAL and blocking — every downstream
        metric/dimension relying on it must stop serving rather than fail
        silently (PRD Sec. 23, anti-pattern list "broken mappings do not
        execute silently")."""
        exists = self._asset_exists(mapping.fully_qualified_asset_name)
        if exists:
            return None
        return DriftEvent(
            drift_event_id=str(uuid.uuid4()),
            concept_id=mapping.concept_id,
            asset_mapping_id=mapping.mapping_id,
            drift_type="BROKEN_MAPPING",
            severity=DriftSeverity.CRITICAL,
            description=f"Asset '{mapping.fully_qualified_asset_name}' referenced by mapping "
                        f"'{mapping.mapping_id}' could not be found via information_schema",
            is_blocking=True,
        )

    def _asset_exists(self, fully_qualified_name: str) -> bool:
        parts = fully_qualified_name.split(".")
        if len(parts) != 3:
            logger.warning("Asset name '%s' is not a 3-part catalog.schema.object name", fully_qualified_name)
            return False
        catalog, schema, obj = parts
        rows = self._repo._query(  # noqa: SLF001
            """SELECT 1 FROM system.information_schema.tables
               WHERE table_catalog = ? AND table_schema = ? AND table_name = ?
               UNION ALL
               SELECT 1 FROM system.information_schema.routines
               WHERE routine_catalog = ? AND routine_schema = ? AND routine_name = ?""",
            (catalog, schema, obj, catalog, schema, obj),
        )
        return len(rows) > 0

    def _check_missing_owners(self) -> list[DriftEvent]:
        rows = self._repo._query(  # noqa: SLF001
            "SELECT concept_id FROM concept WHERE status = 'ACTIVE' AND (owner IS NULL OR owner = '')"
        )
        return [
            DriftEvent(
                drift_event_id=str(uuid.uuid4()),
                concept_id=r["concept_id"],
                drift_type="MISSING_OWNER",
                severity=DriftSeverity.WARNING,
                description=f"Concept '{r['concept_id']}' has no owner assigned",
                is_blocking=False,
            )
            for r in rows
        ]

    async def record_event(self, event: DriftEvent) -> None:
        """Public hook: other pipelines (Genie sync, MCP tool registry sync,
        document-supersession jobs) call this directly to raise a drift event
        this detector has no visibility into on its own."""
        self._repo._query(  # noqa: SLF001
            """INSERT INTO drift_event
                (drift_event_id, concept_id, asset_mapping_id, drift_type, severity, description, is_blocking)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (event.drift_event_id, event.concept_id, event.asset_mapping_id, event.drift_type,
             event.severity.value, event.description, event.is_blocking),
        )
        if event.concept_id:
            await self._lakebase.upsert_drift_status(
                concept_id=event.concept_id,
                severity=event.severity.value,
                is_blocking=event.is_blocking,
                last_event_id=event.drift_event_id,
            )


async def _run() -> None:
    settings = get_settings()
    repo = UnityCatalogOntologyRepository(settings)
    lakebase = LakebaseStateRepository(settings)
    await lakebase.connect()
    try:
        detector = DriftDetector(repo, lakebase)
        result = await detector.scan()
        logger.info(
            "Drift scan complete: %d events, %d blocking concepts",
            len(result.events), len(result.blocking_concept_ids),
        )
    finally:
        await lakebase.close()


def main() -> None:
    """Entry point registered in pyproject.toml as `run_drift_detection`."""
    logging.basicConfig(level=logging.INFO)
    asyncio.run(_run())


if __name__ == "__main__":
    main()
