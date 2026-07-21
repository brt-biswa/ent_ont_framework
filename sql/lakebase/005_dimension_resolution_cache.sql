-- =============================================================================
-- ontology_state.dimension_resolution_cache
--
-- Short-lived cache of resolved dimension/hierarchy values (PRD Sec. 13,
-- example: "Europe enterprise sales" -> SH-EMEA-ENTERPRISE). Resolution is
-- expensive (fuzzy match + hierarchy traversal + OBO-scoped authorization
-- filtering) so successful resolutions are cached briefly, scoped per caller
-- because authorization can change which candidates are visible.
-- =============================================================================

CREATE TABLE IF NOT EXISTS ontology_state.dimension_resolution_cache (
    cache_key           TEXT PRIMARY KEY,        -- hash(dimension_id, input_text, principal_hash, ontology_version)
    dimension_id          TEXT NOT NULL,
    principal_hash         TEXT NOT NULL,
    result                  JSONB NOT NULL,         -- list of {canonical_id, display_name, hierarchy_path, authorized}
    confidence               NUMERIC(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    ontology_version        TEXT NOT NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at               TIMESTAMPTZ NOT NULL,

    CONSTRAINT ck_dim_resolution_bounded_size CHECK (octet_length(result::text) <= 65536)
);

CREATE INDEX IF NOT EXISTS ix_dim_resolution_cache_expires_at
    ON ontology_state.dimension_resolution_cache (expires_at);

CREATE INDEX IF NOT EXISTS ix_dim_resolution_cache_dimension
    ON ontology_state.dimension_resolution_cache (dimension_id, principal_hash);

COMMENT ON TABLE ontology_state.dimension_resolution_cache IS
  'Short-TTL cache of governed dimension-value / hierarchy-node resolution '
  'results, scoped per caller entitlement (a value authorized for one user '
  'may not be authorized for another).';
