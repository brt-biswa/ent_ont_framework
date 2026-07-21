CREATE TABLE IF NOT EXISTS ${catalog}.ontology.change_request (
    change_request_id             STRING NOT NULL,
    concept_id                        STRING,
    business_reason                      STRING NOT NULL,
    old_definition                          STRING,
    new_definition                             STRING NOT NULL,
    effective_date                                DATE NOT NULL,
    affected_metric_ids                              ARRAY<STRING>,
    affected_dimension_ids                              ARRAY<STRING>,
    affected_asset_mapping_ids                             ARRAY<STRING>,
    affected_agent_ids                                        ARRAY<STRING>,
    affected_tool_ids                                            ARRAY<STRING>,
    affected_test_question_ids                                      ARRAY<STRING>,
    migration_plan                                                     STRING,
    stage                                                                 STRING NOT NULL DEFAULT 'SUBMITTED' COMMENT 'SUBMITTED|DOMAIN_REVIEW|DATA_REVIEW|SECURITY_REVIEW|APPROVED|REJECTED|IMPLEMENTED',
    submitted_by                                                             STRING NOT NULL,
    submitted_at                                                                TIMESTAMP NOT NULL DEFAULT current_timestamp()
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Change-request workflow — system of record. Mirrored to Lakebase ontology_state.change_workflow for fast admin-UI reads.';

ALTER TABLE ${catalog}.ontology.change_request ADD CONSTRAINT pk_change_request PRIMARY KEY (change_request_id);
