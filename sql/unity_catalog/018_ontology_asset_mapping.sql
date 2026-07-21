CREATE TABLE IF NOT EXISTS ${catalog}.ontology.asset_mapping (
    mapping_id                    STRING NOT NULL,
    concept_id                       STRING NOT NULL,
    asset_type                          STRING NOT NULL COMMENT 'TABLE|VIEW|MATERIALIZED_VIEW|METRIC_VIEW|COLUMN|MEASURE|DIMENSION_FIELD|UC_FUNCTION|MODEL|MODEL_SERVICE|AI_SEARCH_INDEX|VOLUME|DOCUMENT|GENIE_AGENT|MCP_SERVICE|MCP_TOOL|API|EXTERNAL_APPLICATION',
    fully_qualified_asset_name              STRING NOT NULL,
    field_measure_or_function                  STRING,
    mapping_expression                            STRING,
    approved_join                                    STRING,
    source_system                                       STRING,
    freshness_sla_minutes                                  INT,
    is_certified                                              BOOLEAN NOT NULL DEFAULT FALSE,
    data_quality_state                                          STRING NOT NULL DEFAULT 'UNKNOWN',
    owner                                                          STRING NOT NULL,
    status                                                            STRING NOT NULL DEFAULT 'DRAFT',
    effective_from                                                      DATE NOT NULL,
    effective_to                                                          DATE,
    version                                                                 INT NOT NULL DEFAULT 1,
    created_at                                                                TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_at                                                                  TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_by                                                                    STRING
)
USING DELTA
PARTITIONED BY (asset_type)
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Concept -> physical asset mappings across every supported asset type. Drift detection scans this table.';

ALTER TABLE ${catalog}.ontology.asset_mapping ADD CONSTRAINT pk_asset_mapping PRIMARY KEY (mapping_id, version);
ALTER TABLE ${catalog}.ontology.asset_mapping ADD CONSTRAINT fk_asset_mapping_concept FOREIGN KEY (concept_id) REFERENCES ${catalog}.ontology.concept (concept_id);
