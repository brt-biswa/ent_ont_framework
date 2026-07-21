-- =============================================================================
-- ontology.concept — PRD Sec. 6.1 business concept layer, Sec. 21 data model.
-- The canonical "what does the enterprise mean by X" registry. concept_id is
-- stable for the life of the concept; changes create a new version row
-- (design principle 4: definitions are versioned and effective-dated).
-- =============================================================================
CREATE TABLE IF NOT EXISTS ${catalog}.ontology.concept (
    concept_id           STRING NOT NULL COMMENT 'Stable canonical ID, e.g. METRIC.NET_REVENUE',
    canonical_name        STRING NOT NULL,
    concept_type            STRING NOT NULL COMMENT 'ENTITY|MEASURE|DIMENSION|HIERARCHY|EVENT|STATE|POLICY|RULE|ACTION|CAPABILITY|TIME_CONCEPT|LOCATION|ROLE|DATA_PRODUCT|AGENT|TOOL',
    definition               STRING NOT NULL,
    domain                    STRING NOT NULL,
    subdomain                  STRING,
    owner                        STRING NOT NULL,
    steward                       STRING,
    authority_level               STRING NOT NULL COMMENT '1_CERTIFIED_METRIC_VIEW_OR_FUNCTION..7_USER_CREATED_OR_INFERRED',
    sensitivity                    STRING NOT NULL DEFAULT 'INTERNAL' COMMENT 'PUBLIC|INTERNAL|CONFIDENTIAL|RESTRICTED|REGULATED',
    discoverability                  STRING NOT NULL DEFAULT 'REQUEST_ACCESS' COMMENT 'OPEN|REQUEST_ACCESS|HIDDEN',
    required_group                    STRING COMMENT 'Account group required when discoverability=REQUEST_ACCESS',
    status                              STRING NOT NULL DEFAULT 'DRAFT' COMMENT 'DRAFT|DOMAIN_REVIEW|DATA_REVIEW|SECURITY_REVIEW|APPROVED|ACTIVE|DEPRECATED|RETIRED',
    effective_from                       DATE NOT NULL,
    effective_to                          DATE,
    version                                 INT NOT NULL DEFAULT 1,
    examples                                 ARRAY<STRING>,
    non_examples                              ARRAY<STRING>,
    created_at                                 TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_at                                  TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_by                                   STRING
)
USING DELTA
PARTITIONED BY (domain)
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.columnMapping.mode' = 'name'
)
COMMENT 'Canonical business concepts. concept_id is the stable join key referenced by every other ontology.* table.';

ALTER TABLE ${catalog}.ontology.concept ADD CONSTRAINT pk_concept PRIMARY KEY (concept_id, version);
