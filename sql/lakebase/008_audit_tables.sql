-- =============================================================================
-- audit.* — low-latency operational audit log in Lakebase.
--
-- Every request must record what happened (PRD Sec. 25). Writes here are the
-- fast path used by the API/MCP server at request time; audit/audit_writer.py
-- fans the SAME event out to the equivalent Delta table in Unity Catalog
-- (sql/unity_catalog/030_audit_tables.sql) for immutable, long-term,
-- governance-grade retention. Lakebase rows may be pruned by retention
-- policy; Delta rows are not.
--
-- Hard rule: never log OAuth tokens, secrets, unrestricted sensitive values,
-- or chain-of-thought (PRD Sec. 25, last line) — enforced with the same
-- defense-in-depth CHECK pattern used on the state tables above.
-- =============================================================================

CREATE TABLE IF NOT EXISTS audit.ontology_resolution (
    event_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id       TEXT NOT NULL,
    payload         JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_ontology_resolution_no_token CHECK (
        payload::text !~* '"(access_token|oauth_token|refresh_token|obo_token|password)"'
    )
);

CREATE TABLE IF NOT EXISTS audit.semantic_plan (
    event_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id       TEXT NOT NULL,
    payload         JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_semantic_plan_no_token CHECK (
        payload::text !~* '"(access_token|oauth_token|refresh_token|obo_token|password)"'
    )
);

CREATE TABLE IF NOT EXISTS audit.plan_validation (
    event_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id       TEXT NOT NULL,
    payload         JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_plan_validation_no_token CHECK (
        payload::text !~* '"(access_token|oauth_token|refresh_token|obo_token|password)"'
    )
);

CREATE TABLE IF NOT EXISTS audit.dimension_resolution (
    event_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id       TEXT NOT NULL,
    payload         JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_dimension_resolution_no_token CHECK (
        payload::text !~* '"(access_token|oauth_token|refresh_token|obo_token|password)"'
    )
);

CREATE TABLE IF NOT EXISTS audit.sql_generation (
    event_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id       TEXT NOT NULL,
    payload         JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_sql_generation_no_token CHECK (
        payload::text !~* '"(access_token|oauth_token|refresh_token|obo_token|password)"'
    )
);

CREATE TABLE IF NOT EXISTS audit.sql_validation (
    event_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id       TEXT NOT NULL,
    payload         JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_sql_validation_no_token CHECK (
        payload::text !~* '"(access_token|oauth_token|refresh_token|obo_token|password)"'
    )
);

CREATE TABLE IF NOT EXISTS audit.ontology_change (
    event_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id       TEXT NOT NULL,
    payload         JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_ontology_change_no_token CHECK (
        payload::text !~* '"(access_token|oauth_token|refresh_token|obo_token|password)"'
    )
);

CREATE TABLE IF NOT EXISTS audit.mapping_drift (
    event_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id       TEXT NOT NULL,
    payload         JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_mapping_drift_no_token CHECK (
        payload::text !~* '"(access_token|oauth_token|refresh_token|obo_token|password)"'
    )
);

-- One index pattern shared by every audit table: trace_id lookups (support
-- tickets, incident review) and time-bounded scans (retention jobs, dashboards).
CREATE INDEX IF NOT EXISTS ix_audit_ontology_resolution_trace ON audit.ontology_resolution (trace_id);
CREATE INDEX IF NOT EXISTS ix_audit_ontology_resolution_time  ON audit.ontology_resolution (created_at);

CREATE INDEX IF NOT EXISTS ix_audit_semantic_plan_trace ON audit.semantic_plan (trace_id);
CREATE INDEX IF NOT EXISTS ix_audit_semantic_plan_time  ON audit.semantic_plan (created_at);

CREATE INDEX IF NOT EXISTS ix_audit_plan_validation_trace ON audit.plan_validation (trace_id);
CREATE INDEX IF NOT EXISTS ix_audit_plan_validation_time  ON audit.plan_validation (created_at);

CREATE INDEX IF NOT EXISTS ix_audit_dimension_resolution_trace ON audit.dimension_resolution (trace_id);
CREATE INDEX IF NOT EXISTS ix_audit_dimension_resolution_time  ON audit.dimension_resolution (created_at);

CREATE INDEX IF NOT EXISTS ix_audit_sql_generation_trace ON audit.sql_generation (trace_id);
CREATE INDEX IF NOT EXISTS ix_audit_sql_generation_time  ON audit.sql_generation (created_at);

CREATE INDEX IF NOT EXISTS ix_audit_sql_validation_trace ON audit.sql_validation (trace_id);
CREATE INDEX IF NOT EXISTS ix_audit_sql_validation_time  ON audit.sql_validation (created_at);

CREATE INDEX IF NOT EXISTS ix_audit_ontology_change_trace ON audit.ontology_change (trace_id);
CREATE INDEX IF NOT EXISTS ix_audit_ontology_change_time  ON audit.ontology_change (created_at);

CREATE INDEX IF NOT EXISTS ix_audit_mapping_drift_trace ON audit.mapping_drift (trace_id);
CREATE INDEX IF NOT EXISTS ix_audit_mapping_drift_time  ON audit.mapping_drift (created_at);
