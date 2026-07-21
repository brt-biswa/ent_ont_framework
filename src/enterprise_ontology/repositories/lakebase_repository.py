"""Lakebase-backed repository — the application's operational database.

Lakebase (Databricks' managed, Postgres-compatible OLTP store) holds
everything that must be read/written with low latency at request time and
that does NOT belong in the governed, append-mostly Unity Catalog Delta
tables: active-version pointers, compiled ontology snapshots, per-user
projection caches, dimension-resolution result caches, the change-request
workflow queue, and drift status (PRD Sec. 21 "Operational Lakebase tables").

Hard rules enforced by this module (PRD Sec. 9, 19):
  * OAuth/OBO tokens are NEVER written to any Lakebase table.
  * Only small, reconstructable metadata is cached — no full ontology, no
    unbounded categorical value sets.
  * Every cache row carries the ontology_version + policy_version it was
    computed against, so a version bump invalidates it deterministically.

DDL for every table this class touches lives in sql/lakebase/.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import asyncpg

from ..config import Settings, get_settings

logger = logging.getLogger(__name__)


class LakebaseStateRepository:
    """Async connection-pooled access to the `ontology_state` and `audit` schemas
    in Lakebase. One instance should be created per process and reused."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        if self._pool is not None:
            return
        s = self.settings
        # Prefer a short-lived Databricks OAuth token over a static password.
        password = s.lakebase_oauth_token or s.lakebase_password
        self._pool = await asyncpg.create_pool(
            host=s.lakebase_host,
            port=s.lakebase_port,
            database=s.lakebase_database,
            user=s.lakebase_user,
            password=password,
            ssl=s.lakebase_sslmode != "disable",
            min_size=s.lakebase_pool_min_size,
            max_size=s.lakebase_pool_max_size,
            command_timeout=s.sql_query_timeout_seconds,
        )

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def _pool_or_connect(self) -> asyncpg.Pool:
        if self._pool is None:
            await self.connect()
        assert self._pool is not None
        return self._pool

    # ---------------------------------------------------------------
    # ontology_state.active_version
    # ---------------------------------------------------------------
    async def get_active_version(self) -> Optional[dict[str, Any]]:
        pool = await self._pool_or_connect()
        row = await pool.fetchrow(
            """SELECT version_id, label, activated_at, activated_by, notes
               FROM ontology_state.active_version
               ORDER BY activated_at DESC LIMIT 1"""
        )
        return dict(row) if row else None

    async def set_active_version(self, version_id: str, label: str, activated_by: str, notes: str = "") -> None:
        pool = await self._pool_or_connect()
        await pool.execute(
            """INSERT INTO ontology_state.active_version
                    (version_id, label, activated_at, activated_by, notes)
               VALUES ($1, $2, now(), $3, $4)
               ON CONFLICT (version_id) DO UPDATE
                    SET activated_at = EXCLUDED.activated_at,
                        activated_by = EXCLUDED.activated_by,
                        notes = EXCLUDED.notes""",
            version_id, label, activated_by, notes,
        )

    # ---------------------------------------------------------------
    # ontology_state.compiled_snapshot  (L1/L2 shared ontology projection)
    # ---------------------------------------------------------------
    async def get_compiled_snapshot(self, snapshot_key: str) -> Optional[dict[str, Any]]:
        pool = await self._pool_or_connect()
        row = await pool.fetchrow(
            """SELECT payload, ontology_version, policy_version, expires_at
               FROM ontology_state.compiled_snapshot
               WHERE snapshot_key = $1 AND expires_at > now()""",
            snapshot_key,
        )
        if not row:
            return None
        return {**dict(row), "payload": json.loads(row["payload"])}

    async def put_compiled_snapshot(
        self, snapshot_key: str, payload: dict[str, Any], ontology_version: str,
        policy_version: str, ttl_seconds: Optional[int] = None,
    ) -> None:
        pool = await self._pool_or_connect()
        ttl = ttl_seconds or self.settings.l2_cache_ttl_seconds
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        await pool.execute(
            """INSERT INTO ontology_state.compiled_snapshot
                    (snapshot_key, payload, ontology_version, policy_version, created_at, expires_at)
               VALUES ($1, $2::jsonb, $3, $4, now(), $5)
               ON CONFLICT (snapshot_key) DO UPDATE
                    SET payload = EXCLUDED.payload,
                        ontology_version = EXCLUDED.ontology_version,
                        policy_version = EXCLUDED.policy_version,
                        created_at = now(),
                        expires_at = EXCLUDED.expires_at""",
            snapshot_key, json.dumps(payload), ontology_version, policy_version, expires_at,
        )

    # ---------------------------------------------------------------
    # ontology_state.user_projection_cache  (per-user permission-aware projection)
    # ---------------------------------------------------------------
    async def get_user_projection(self, cache_key: str) -> Optional[dict[str, Any]]:
        """cache_key MUST be built from entitlement_scope_hash(), never a raw
        user id alone and never the OBO token (PRD Sec. 19)."""
        pool = await self._pool_or_connect()
        row = await pool.fetchrow(
            """SELECT projection, ontology_version, policy_version
               FROM ontology_state.user_projection_cache
               WHERE cache_key = $1 AND expires_at > now()""",
            cache_key,
        )
        return {**dict(row), "projection": json.loads(row["projection"])} if row else None

    async def put_user_projection(
        self, cache_key: str, principal_hash: str, projection: dict[str, Any],
        ontology_version: str, policy_version: str, ttl_seconds: Optional[int] = None,
    ) -> None:
        pool = await self._pool_or_connect()
        ttl = ttl_seconds or self.settings.l2_cache_ttl_seconds
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        await pool.execute(
            """INSERT INTO ontology_state.user_projection_cache
                    (cache_key, principal_hash, projection, ontology_version, policy_version,
                     created_at, expires_at)
               VALUES ($1, $2, $3::jsonb, $4, $5, now(), $6)
               ON CONFLICT (cache_key) DO UPDATE
                    SET projection = EXCLUDED.projection,
                        ontology_version = EXCLUDED.ontology_version,
                        policy_version = EXCLUDED.policy_version,
                        created_at = now(),
                        expires_at = EXCLUDED.expires_at""",
            cache_key, principal_hash, json.dumps(projection), ontology_version, policy_version, expires_at,
        )

    # ---------------------------------------------------------------
    # ontology_state.dimension_resolution_cache
    # ---------------------------------------------------------------
    async def get_dimension_resolution(self, cache_key: str) -> Optional[dict[str, Any]]:
        pool = await self._pool_or_connect()
        row = await pool.fetchrow(
            """SELECT result, confidence, ontology_version
               FROM ontology_state.dimension_resolution_cache
               WHERE cache_key = $1 AND expires_at > now()""",
            cache_key,
        )
        return {**dict(row), "result": json.loads(row["result"])} if row else None

    async def put_dimension_resolution(
        self, cache_key: str, dimension_id: str, principal_hash: str,
        result: dict[str, Any], confidence: float, ontology_version: str,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        pool = await self._pool_or_connect()
        ttl = ttl_seconds or self.settings.l2_cache_ttl_seconds
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        await pool.execute(
            """INSERT INTO ontology_state.dimension_resolution_cache
                    (cache_key, dimension_id, principal_hash, result, confidence,
                     ontology_version, created_at, expires_at)
               VALUES ($1, $2, $3, $4::jsonb, $5, $6, now(), $7)
               ON CONFLICT (cache_key) DO UPDATE
                    SET result = EXCLUDED.result,
                        confidence = EXCLUDED.confidence,
                        ontology_version = EXCLUDED.ontology_version,
                        created_at = now(),
                        expires_at = EXCLUDED.expires_at""",
            cache_key, dimension_id, principal_hash, json.dumps(result), confidence,
            ontology_version, expires_at,
        )

    # ---------------------------------------------------------------
    # ontology_state.change_workflow  (lightweight queue mirroring UC change_request)
    # ---------------------------------------------------------------
    async def enqueue_change_workflow(
        self, change_request_id: str, stage: str, assignee_group: Optional[str] = None,
    ) -> None:
        pool = await self._pool_or_connect()
        await pool.execute(
            """INSERT INTO ontology_state.change_workflow
                    (change_request_id, stage, assignee_group, updated_at)
               VALUES ($1, $2, $3, now())
               ON CONFLICT (change_request_id) DO UPDATE
                    SET stage = EXCLUDED.stage,
                        assignee_group = EXCLUDED.assignee_group,
                        updated_at = now()""",
            change_request_id, stage, assignee_group,
        )

    async def list_pending_change_workflow(self, stage: Optional[str] = None) -> list[dict[str, Any]]:
        pool = await self._pool_or_connect()
        if stage:
            rows = await pool.fetch(
                """SELECT * FROM ontology_state.change_workflow WHERE stage = $1
                   ORDER BY updated_at ASC""",
                stage,
            )
        else:
            rows = await pool.fetch(
                """SELECT * FROM ontology_state.change_workflow
                   WHERE stage NOT IN ('APPROVED','REJECTED','IMPLEMENTED')
                   ORDER BY updated_at ASC"""
            )
        return [dict(r) for r in rows]

    # ---------------------------------------------------------------
    # ontology_state.drift_status  (fast-read mirror of latest drift per concept)
    # ---------------------------------------------------------------
    async def upsert_drift_status(
        self, concept_id: str, severity: str, is_blocking: bool, last_event_id: str,
    ) -> None:
        pool = await self._pool_or_connect()
        await pool.execute(
            """INSERT INTO ontology_state.drift_status
                    (concept_id, severity, is_blocking, last_event_id, updated_at)
               VALUES ($1, $2, $3, $4, now())
               ON CONFLICT (concept_id) DO UPDATE
                    SET severity = EXCLUDED.severity,
                        is_blocking = EXCLUDED.is_blocking,
                        last_event_id = EXCLUDED.last_event_id,
                        updated_at = now()""",
            concept_id, severity, is_blocking, last_event_id,
        )

    async def get_blocking_concepts(self) -> list[str]:
        pool = await self._pool_or_connect()
        rows = await pool.fetch(
            "SELECT concept_id FROM ontology_state.drift_status WHERE is_blocking = true"
        )
        return [r["concept_id"] for r in rows]

    # ---------------------------------------------------------------
    # audit.* writes (fast path; long-term/immutable copy also lands in Delta —
    # see audit/audit_writer.py which fans out to both)
    # ---------------------------------------------------------------
    async def write_audit_event(self, table: str, event: dict[str, Any]) -> None:
        allowed_tables = {
            "ontology_resolution", "semantic_plan", "plan_validation",
            "dimension_resolution", "sql_generation", "sql_validation",
            "ontology_change", "mapping_drift",
        }
        if table not in allowed_tables:
            raise ValueError(f"Unknown audit table: {table}")
        pool = await self._pool_or_connect()
        await pool.execute(
            f"""INSERT INTO audit.{table} (event_id, trace_id, payload, created_at)
                VALUES ($1, $2, $3::jsonb, now())""",
            event["event_id"], event.get("trace_id"), json.dumps(event),
        )
