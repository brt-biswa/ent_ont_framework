CREATE TABLE IF NOT EXISTS ${catalog}.ontology.drift_event (
    drift_event_id       STRING NOT NULL,
    concept_id               STRING,
    asset_mapping_id            STRING,
    drift_type                     STRING NOT NULL COMMENT 'MISSING_TABLE|RENAMED_COLUMN|METRIC_DEF_CHANGE|FUNCTION_CHANGE|HIERARCHY_CHANGE|NEW_CATEGORICAL_VALUE|DEPRECATED_SOURCE_IN_USE|BROKEN_MAPPING|GENIE_CHANGE|TOOL_SCHEMA_CHANGE|SUPERSEDED_DOCUMENT|CONFLICTING_DEFINITION|SECURITY_TAG_CHANGE|MISSING_OWNER',
    severity                          STRING NOT NULL COMMENT 'INFO|WARNING|CRITICAL',
    description                          STRING NOT NULL,
    detected_at                              TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    is_blocking                                 BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at                                    TIMESTAMP,
    resolved_by                                       STRING
)
USING DELTA
PARTITIONED BY (severity)
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Full drift event history (Sec. 23). Latest per-concept status mirrored to Lakebase ontology_state.drift_status.';

ALTER TABLE ${catalog}.ontology.drift_event ADD CONSTRAINT pk_drift_event PRIMARY KEY (drift_event_id);
