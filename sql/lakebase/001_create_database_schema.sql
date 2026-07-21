-- =============================================================================
-- Lakebase bootstrap — the application's operational (OLTP) database.
-- Lakebase is Databricks' managed, Postgres-compatible store. This file and
-- the ones that follow (002-008) create the `ontology_state` and `audit`
-- schemas that back repositories/lakebase_repository.py.
--
-- Run order: 001 -> 002 -> 003 -> 004 -> 005 -> 006 -> 007 -> 008
-- (or via the bootstrap_lakebase job entry point, which runs them in order).
--
-- Design rules enforced by this schema (PRD Sec. 9, 19, 21):
--   * No OAuth/OBO tokens are ever stored here — every table is checked in
--     review for a token/secret column before merge.
--   * Every cache table carries ontology_version + policy_version and an
--     explicit expires_at so state is always reconstructable and never
--     silently stale.
--   * cache_key columns are built from a principal ENTITLEMENT hash
--     (see models/context.py UserContext.entitlement_scope_hash), never a
--     raw user id and never a token.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS ontology_state;
CREATE SCHEMA IF NOT EXISTS audit;

-- Extension used for gen_random_uuid() default values below.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

COMMENT ON SCHEMA ontology_state IS
  'Operational state for the Enterprise Ontology Framework: active version pointer, '
  'compiled snapshots, per-user projection cache, dimension-resolution cache, '
  'change-request workflow queue, drift status. Application database (Lakebase) — '
  'not the system of record. System of record for governed definitions is Unity '
  'Catalog (see sql/unity_catalog/).';

COMMENT ON SCHEMA audit IS
  'Low-latency operational audit log (fast writes/reads for the API/MCP server). '
  'Fanned out from the same events also written immutably to Delta audit tables '
  'in Unity Catalog for long-term, tamper-evident retention.';
