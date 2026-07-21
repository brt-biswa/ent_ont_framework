CREATE TABLE IF NOT EXISTS ${catalog}.ontology.security_scope (
    scope_id                   STRING NOT NULL,
    concept_id                    STRING,
    dimension_id                     STRING,
    sensitivity                         STRING NOT NULL COMMENT 'PUBLIC|INTERNAL|CONFIDENTIAL|RESTRICTED|REGULATED',
    required_group                         STRING,
    row_filter_expression                     STRING,
    column_mask_expression                       STRING,
    requires_obo                                    BOOLEAN NOT NULL DEFAULT FALSE,
    owner                                               STRING NOT NULL,
    status                                                 STRING NOT NULL DEFAULT 'DRAFT',
    effective_from                                            DATE NOT NULL,
    effective_to                                                DATE,
    version                                                       INT NOT NULL DEFAULT 1,
    created_at                                                      TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_at                                                        TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_by                                                          STRING
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'ABAC scope definitions: row filters, column masks, required groups per concept/dimension.';

ALTER TABLE ${catalog}.ontology.security_scope ADD CONSTRAINT pk_security_scope PRIMARY KEY (scope_id, version);
