-- =============================================================================
-- ontology_state.drift_status
--
-- Latest-known-drift-state-per-concept, read on the hot path so that plan
-- validation (sql_policy / planner) can cheaply block use of a concept whose
-- mapping is currently broken (PRD Sec. 23: "Critical drift must block
-- production use of affected concepts or metrics"). The full drift event
-- history is ontology.drift_event in Unity Catalog; this table is a fast
-- "is concept X currently blocked" lookup.
-- =============================================================================

CREATE TABLE IF NOT EXISTS ontology_state.drift_status (
    concept_id       TEXT PRIMARY KEY,
    severity            TEXT NOT NULL CHECK (severity IN ('INFO', 'WARNING', 'CRITICAL')),
    is_blocking          BOOLEAN NOT NULL DEFAULT FALSE,
    last_event_id         TEXT NOT NULL,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_drift_status_blocking
    ON ontology_state.drift_status (is_blocking)
    WHERE is_blocking = TRUE;

COMMENT ON TABLE ontology_state.drift_status IS
  'Fast "is this concept currently blocked by critical drift" lookup used by '
  'the semantic validator on every request. Full history: ontology.drift_event.';
