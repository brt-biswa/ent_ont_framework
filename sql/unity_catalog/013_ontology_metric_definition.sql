-- =============================================================================
-- ontology.metric_definition — PRD Sec. 6.3. certified_source_asset points at
-- the ONE executable asset (metric view / UC function / trusted SQL) that
-- implements this metric. The LLM must never invent the formula (Sec. 10).
-- =============================================================================
CREATE TABLE IF NOT EXISTS ${catalog}.ontology.metric_definition (
    metric_id                STRING NOT NULL COMMENT 'e.g. METRIC.NET_REVENUE',
    concept_id                  STRING NOT NULL,
    business_definition            STRING NOT NULL,
    formula                           STRING NOT NULL COMMENT 'Human-readable formula for explainability, not for execution',
    aggregation_behavior                 STRING NOT NULL COMMENT 'SUM|AVG|COUNT_DISTINCT|non-additive, etc.',
    allowed_dimension_ids                   ARRAY<STRING> NOT NULL,
    prohibited_dimension_ids                   ARRAY<STRING>,
    time_grain                                    STRING NOT NULL DEFAULT 'MONTH' COMMENT 'DAY|WEEK|MONTH|FISCAL_PERIOD|QUARTER|FISCAL_YEAR|YEAR',
    currency                                         STRING,
    unit                                                STRING,
    comparison_rules                                       ARRAY<STRING>,
    materiality_threshold                                     DOUBLE,
    certified_source_asset                                       STRING NOT NULL COMMENT 'Fully qualified metric view / UC function / trusted SQL asset',
    is_certified                                                    BOOLEAN NOT NULL DEFAULT FALSE,
    owner                                                              STRING NOT NULL,
    steward                                                               STRING,
    sensitivity                                                             STRING NOT NULL DEFAULT 'INTERNAL',
    discoverability                                                           STRING NOT NULL DEFAULT 'REQUEST_ACCESS',
    status                                                                      STRING NOT NULL DEFAULT 'DRAFT',
    effective_from                                                               DATE NOT NULL,
    effective_to                                                                  DATE,
    version                                                                         INT NOT NULL DEFAULT 1,
    created_at                                                                       TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_at                                                                        TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_by                                                                         STRING
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Certified metric registry — one governed formula and source asset per metric_id.';

ALTER TABLE ${catalog}.ontology.metric_definition ADD CONSTRAINT pk_metric_definition PRIMARY KEY (metric_id, version);
ALTER TABLE ${catalog}.ontology.metric_definition ADD CONSTRAINT fk_metric_concept FOREIGN KEY (concept_id) REFERENCES ${catalog}.ontology.concept (concept_id);
