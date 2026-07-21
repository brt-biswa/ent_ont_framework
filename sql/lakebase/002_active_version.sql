-- =============================================================================
-- ontology_state.active_version
--
-- Single fast-read pointer to "which ontology version is currently ACTIVE".
-- The system of record for version history and lifecycle transitions is
-- ontology.version + ontology.approval_history in Unity Catalog; this table
-- is the low-latency mirror the API/MCP server reads on every request so it
-- never has to hit the SQL warehouse in the hot path.
-- =============================================================================

CREATE TABLE IF NOT EXISTS ontology_state.active_version (
    version_id      TEXT PRIMARY KEY,
    label           TEXT NOT NULL,                    -- e.g. '2026.07.1'
    activated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    activated_by    TEXT NOT NULL,
    notes           TEXT,
    is_current      BOOLEAN NOT NULL DEFAULT TRUE
);

-- Only one row should ever be "current" at a time. Enforced via a partial
-- unique index rather than a boolean-flip trigger, to keep writes simple
-- (the repository always upserts, and a scheduled job in Epic 8's admin flow
-- clears older rows' is_current flag when activating a new version).
CREATE UNIQUE INDEX IF NOT EXISTS ux_active_version_current
    ON ontology_state.active_version (is_current)
    WHERE is_current = TRUE;

CREATE INDEX IF NOT EXISTS ix_active_version_activated_at
    ON ontology_state.active_version (activated_at DESC);

COMMENT ON TABLE ontology_state.active_version IS
  'Fast-read pointer to the currently ACTIVE ontology version label. Mirrors '
  'ontology.version (Unity Catalog) is_active=true row.';
