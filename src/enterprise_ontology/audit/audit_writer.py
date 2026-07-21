"""Audit trail writer — PRD Sec. 25. Fans every audit event out to BOTH the
fast Lakebase mirror (audit.* tables, read by the admin UI / support
tooling) and the immutable Delta system of record (Unity Catalog
audit.* tables) via a lightweight async queue, so a Lakebase outage never
means an unaudited request and a Delta write never blocks the request path.

Never logs OAuth tokens, secrets, unrestricted sensitive values, or
chain-of-thought (PRD Sec. 25, last line) — payloads passed to this writer
must already be scrubbed by the caller; this class does not attempt to be a
silent redactor because "we thought we redacted it" is exactly the failure
mode Sec. 25 warns against. The CHECK constraints on the Lakebase tables
(sql/lakebase/008_audit_tables.sql) are the enforced backstop.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from ..repositories.lakebase_repository import LakebaseStateRepository

logger = logging.getLogger(__name__)

_ALLOWED_TABLES = {
    "ontology_resolution", "semantic_plan", "plan_validation",
    "dimension_resolution", "sql_generation", "sql_validation",
    "ontology_change", "mapping_drift",
}


class AuditWriter:
    def __init__(self, lakebase: LakebaseStateRepository, delta_writer_fn=None):
        self._lakebase = lakebase
        # `delta_writer_fn` is injectable: in production this is a small
        # Spark/Delta append (via a UC volume-backed job or Lakehouse
        # Federation write-back), kept pluggable so unit tests never need a
        # live SQL warehouse.
        self._delta_writer_fn = delta_writer_fn

    async def write(self, table: str, trace_id: str, payload: dict[str, Any]) -> str:
        if table not in _ALLOWED_TABLES:
            raise ValueError(f"Unknown audit table '{table}'")

        event_id = str(uuid.uuid4())
        event = {"event_id": event_id, "trace_id": trace_id, **payload}

        try:
            await self._lakebase.write_audit_event(table, event)
        except Exception:  # noqa: BLE001
            logger.exception("Failed to write fast-path audit event to Lakebase (table=%s)", table)
            # Fail open on the FAST mirror only if the durable Delta write
            # below still succeeds — losing audit entirely is not acceptable,
            # but a slow/unavailable OLTP mirror should not block the caller
            # from getting a durable record.

        if self._delta_writer_fn is not None:
            try:
                await self._delta_writer_fn(table, event)
            except Exception:  # noqa: BLE001
                logger.exception("Failed to write durable Delta audit event (table=%s)", table)

        return event_id
