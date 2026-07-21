-- =============================================================================
-- ontology_state.compiled_snapshot
--
-- L2 cache (PRD Sec. 19 "L2 Lakebase") for SHARED, non-user-specific compiled
-- ontology projections: the approved join graph, small metric/dimension
-- metadata bundles, domain-level "core context" bundles used to seed the
-- planner's static prompt content. Bounded, TTL'd, reconstructable from
-- Unity Catalog at any time — never the sole source of truth.
-- =============================================================================

CREATE TABLE IF NOT EXISTS ontology_state.compiled_snapshot (
    snapshot_key        TEXT PRIMARY KEY,        -- e.g. 'domain:finance:core_context:v2026.07.1'
    payload              JSONB NOT NULL,
    ontology_version     TEXT NOT NULL,
    policy_version        TEXT NOT NULL,
    size_bytes            INTEGER GENERATED ALWAYS AS (octet_length(payload::text)) STORED,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at            TIMESTAMPTZ NOT NULL,

    -- Caches must stay small and reconstructable (PRD Sec. 19). 256 KB is a
    -- generous ceiling for a "small ontology projection" — anything bigger is
    -- a sign the caller should be paging or narrowing scope, not caching more.
    CONSTRAINT ck_compiled_snapshot_bounded_size CHECK (octet_length(payload::text) <= 262144)
);

CREATE INDEX IF NOT EXISTS ix_compiled_snapshot_expires_at
    ON ontology_state.compiled_snapshot (expires_at);

CREATE INDEX IF NOT EXISTS ix_compiled_snapshot_version
    ON ontology_state.compiled_snapshot (ontology_version, policy_version);

COMMENT ON TABLE ontology_state.compiled_snapshot IS
  'L2 cache of small, shared, reconstructable ontology projections keyed by a '
  'domain/purpose/version composite key. No user-specific or sensitive data — '
  'see user_projection_cache for that.';
