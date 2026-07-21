-- =============================================================================
-- ontology.dimension_definition — PRD Sec. 6.3.
-- =============================================================================
CREATE TABLE IF NOT EXISTS ${catalog}.ontology.dimension_definition (
    dimension_id          STRING NOT NULL COMMENT 'e.g. ORG.OPERATING_UNIT',
    concept_id                STRING NOT NULL,
    key_column                   STRING NOT NULL,
    label_column                    STRING,
    hierarchy_id                       STRING,
    allowed_operators                     ARRAY<STRING> NOT NULL COMMENT 'EQUALS|NOT_EQUALS|IN|NOT_IN|GREATER_THAN|...|CONTAINS_HIERARCHY_PATH',
    value_resolution_strategy               STRING NOT NULL DEFAULT 'EXACT_MATCH' COMMENT 'EXACT_MATCH|FUZZY_MATCH|SYNONYM_LOOKUP|HIERARCHY_PATH|OBO_GOVERNED_SERVICE',
    high_cardinality                            BOOLEAN NOT NULL DEFAULT FALSE,
    requires_obo                                   BOOLEAN NOT NULL DEFAULT FALSE,
    owner                                             STRING NOT NULL,
    steward                                              STRING,
    sensitivity                                            STRING NOT NULL DEFAULT 'INTERNAL',
    discoverability                                          STRING NOT NULL DEFAULT 'REQUEST_ACCESS',
    status                                                     STRING NOT NULL DEFAULT 'DRAFT',
    effective_from                                              DATE NOT NULL,
    effective_to                                                 DATE,
    version                                                        INT NOT NULL DEFAULT 1,
    created_at                                                      TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_at                                                       TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_by                                                        STRING
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Certified dimension registry — key/label mapping, hierarchy membership, allowed operators, OBO requirement.';

ALTER TABLE ${catalog}.ontology.dimension_definition ADD CONSTRAINT pk_dimension_definition PRIMARY KEY (dimension_id, version);
ALTER TABLE ${catalog}.ontology.dimension_definition ADD CONSTRAINT fk_dimension_concept FOREIGN KEY (concept_id) REFERENCES ${catalog}.ontology.concept (concept_id);
