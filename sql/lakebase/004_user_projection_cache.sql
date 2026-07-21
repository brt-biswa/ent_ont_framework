-- =============================================================================
-- ontology_state.user_projection_cache
--
-- Per-user (per-entitlement-scope) permission-aware ontology projection —
-- the small slice of concepts/metrics/dimensions a specific caller is allowed
-- to see for a specific question/domain, after RBAC/ABAC + ontology
-- discoverability filtering has already been applied (PRD Sec. 12 runtime
-- sequence step 4, design principle 6).
--
-- cache_key is derived from UserContext.entitlement_scope_hash() — a SHA-256
-- hash of (principal_id, sorted entitlement_group_ids), never the raw OAuth
-- token and never persisted alongside the token itself (PRD Sec. 9, 19).
-- =============================================================================

CREATE TABLE IF NOT EXISTS ontology_state.user_projection_cache (
    cache_key            TEXT PRIMARY KEY,
    principal_hash        TEXT NOT NULL,          -- UserContext.entitlement_scope_hash()
    projection             JSONB NOT NULL,
    ontology_version      TEXT NOT NULL,
    policy_version         TEXT NOT NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at             TIMESTAMPTZ NOT NULL,

    CONSTRAINT ck_user_projection_bounded_size CHECK (octet_length(projection::text) <= 262144),
    -- Defense in depth: reject any row that somehow contains a token-shaped field.
    CONSTRAINT ck_user_projection_no_token CHECK (
        projection::text !~* '"(access_token|oauth_token|refresh_token|obo_token)"'
    )
);

CREATE INDEX IF NOT EXISTS ix_user_projection_cache_expires_at
    ON ontology_state.user_projection_cache (expires_at);

CREATE INDEX IF NOT EXISTS ix_user_projection_cache_principal
    ON ontology_state.user_projection_cache (principal_hash);

COMMENT ON TABLE ontology_state.user_projection_cache IS
  'Per-entitlement-scope cache of a permission-aware ontology projection. '
  'NEVER stores an OAuth/OBO token — enforced by ck_user_projection_no_token '
  'as a defense-in-depth check in addition to application-layer discipline.';
