-- =============================================================================
-- audit.* — immutable, append-only Delta audit trail (Sec. 25). This is the
-- long-term system of record; Lakebase audit.* (sql/lakebase/008_audit_tables.sql)
-- is the fast operational mirror the API writes to synchronously, fanned out
-- here asynchronously by audit/audit_writer.py (or a Lakehouse Federation /
-- CDC pipeline in a more mature deployment).
--
-- Every request must record request/trace id, identity, agent+version,
-- ontology+policy version, resolved concepts+confidence, clarification
-- decision, resolved dimension values, semantic plan, validation result,
-- compiler/generator path, SQL-policy decision, physical assets used,
-- OBO/App-SP mode, data freshness, evidence and result metadata (Sec. 25).
-- Never log tokens, secrets, unrestricted sensitive values, or chain-of-thought.
-- =============================================================================

CREATE TABLE IF NOT EXISTS ${catalog}.audit.ontology_resolution (
    event_id     STRING NOT NULL,
    trace_id        STRING NOT NULL,
    principal_hash     STRING NOT NULL COMMENT 'Entitlement-scope hash — never a raw token or PII beyond principal id',
    agent_name             STRING,
    ontology_version          STRING NOT NULL,
    matched_concept_ids          ARRAY<STRING>,
    confidence                       DOUBLE,
    requires_clarification              BOOLEAN,
    created_at                             TIMESTAMP NOT NULL DEFAULT current_timestamp()
)
USING DELTA
PARTITIONED BY (DATE(created_at))
TBLPROPERTIES ('delta.appendOnly' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Immutable audit of concept/synonym resolution decisions.';

CREATE TABLE IF NOT EXISTS ${catalog}.audit.semantic_plan (
    event_id      STRING NOT NULL,
    trace_id         STRING NOT NULL,
    principal_hash      STRING NOT NULL,
    agent_name              STRING,
    ontology_version           STRING NOT NULL,
    plan_json                     STRING NOT NULL COMMENT 'Serialized SemanticPlan — structured, never raw generated SQL or prose',
    created_at                       TIMESTAMP NOT NULL DEFAULT current_timestamp()
)
USING DELTA
PARTITIONED BY (DATE(created_at))
TBLPROPERTIES ('delta.appendOnly' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Immutable audit of every structured plan the planner produced.';

CREATE TABLE IF NOT EXISTS ${catalog}.audit.plan_validation (
    event_id     STRING NOT NULL,
    trace_id        STRING NOT NULL,
    principal_hash     STRING NOT NULL,
    ontology_version      STRING NOT NULL,
    policy_version           STRING NOT NULL,
    is_valid                    BOOLEAN NOT NULL,
    violations                     ARRAY<STRING>,
    created_at                        TIMESTAMP NOT NULL DEFAULT current_timestamp()
)
USING DELTA
PARTITIONED BY (DATE(created_at))
TBLPROPERTIES ('delta.appendOnly' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Immutable audit of validator decisions and violation reasons.';

CREATE TABLE IF NOT EXISTS ${catalog}.audit.dimension_resolution (
    event_id     STRING NOT NULL,
    trace_id        STRING NOT NULL,
    principal_hash     STRING NOT NULL,
    dimension_id          STRING NOT NULL,
    input_text                STRING,
    resolved_canonical_ids       ARRAY<STRING>,
    confidence                       DOUBLE,
    authorized_count                    INT,
    unauthorized_count_removed             INT,
    created_at                                TIMESTAMP NOT NULL DEFAULT current_timestamp()
)
USING DELTA
PARTITIONED BY (DATE(created_at))
TBLPROPERTIES ('delta.appendOnly' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Immutable audit of dimension/hierarchy value resolution, including unauthorized candidates removed.';

CREATE TABLE IF NOT EXISTS ${catalog}.audit.sql_generation (
    event_id     STRING NOT NULL,
    trace_id        STRING NOT NULL,
    principal_hash     STRING NOT NULL,
    generation_path        STRING NOT NULL COMMENT 'DETERMINISTIC_COMPILER|CONSTRAINED_LLM_GENERATION',
    generated_sql_hash          STRING NOT NULL COMMENT 'Hash of generated SQL, not the raw SQL text with literal values',
    assets_used                     ARRAY<STRING>,
    created_at                          TIMESTAMP NOT NULL DEFAULT current_timestamp()
)
USING DELTA
PARTITIONED BY (DATE(created_at))
TBLPROPERTIES ('delta.appendOnly' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Immutable audit of which path (deterministic vs constrained LLM) produced each query and which assets it touched.';

CREATE TABLE IF NOT EXISTS ${catalog}.audit.sql_validation (
    event_id     STRING NOT NULL,
    trace_id        STRING NOT NULL,
    principal_hash     STRING NOT NULL,
    policy_version         STRING NOT NULL,
    passed                     BOOLEAN NOT NULL,
    denied_reasons                 ARRAY<STRING>,
    estimated_row_limit                INT,
    created_at                            TIMESTAMP NOT NULL DEFAULT current_timestamp()
)
USING DELTA
PARTITIONED BY (DATE(created_at))
TBLPROPERTIES ('delta.appendOnly' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Immutable audit of AST/policy-gateway validation outcomes (Sec. 14, 16).';

CREATE TABLE IF NOT EXISTS ${catalog}.audit.ontology_change (
    event_id     STRING NOT NULL,
    change_request_id     STRING NOT NULL,
    stage                     STRING NOT NULL,
    actor                        STRING NOT NULL,
    decision                        STRING,
    created_at                          TIMESTAMP NOT NULL DEFAULT current_timestamp()
)
USING DELTA
PARTITIONED BY (DATE(created_at))
TBLPROPERTIES ('delta.appendOnly' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Immutable audit trail of governance workflow transitions (mirrors ontology.approval_history events as they occur).';

CREATE TABLE IF NOT EXISTS ${catalog}.audit.mapping_drift (
    event_id     STRING NOT NULL,
    drift_event_id     STRING NOT NULL,
    concept_id             STRING,
    drift_type                 STRING NOT NULL,
    severity                       STRING NOT NULL,
    is_blocking                        BOOLEAN NOT NULL,
    created_at                             TIMESTAMP NOT NULL DEFAULT current_timestamp()
)
USING DELTA
PARTITIONED BY (DATE(created_at))
TBLPROPERTIES ('delta.appendOnly' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Immutable audit copy of every drift event raised (Sec. 23).';
