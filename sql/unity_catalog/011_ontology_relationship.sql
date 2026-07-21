-- =============================================================================
-- ontology.relationship — PRD Sec. 6.2. Approved join paths live here
-- (approved_join_ref) so the compiler never has to guess a join.
-- =============================================================================
CREATE TABLE IF NOT EXISTS ${catalog}.ontology.relationship (
    relationship_id     STRING NOT NULL,
    source_concept_id     STRING NOT NULL,
    predicate                STRING NOT NULL COMMENT 'e.g. places, contains, settles, calculated_from, invokes, accesses',
    target_concept_id           STRING NOT NULL,
    cardinality                    STRING NOT NULL COMMENT 'ONE_TO_ONE|ONE_TO_MANY|MANY_TO_ONE|MANY_TO_MANY',
    required                          BOOLEAN NOT NULL DEFAULT FALSE,
    approved_join_ref                    STRING COMMENT 'Fully qualified join expression, e.g. orders.customer_id = customers.customer_id',
    security_implications                  STRING,
    owner                                     STRING NOT NULL,
    steward                                    STRING,
    sensitivity                                 STRING NOT NULL DEFAULT 'INTERNAL',
    discoverability                              STRING NOT NULL DEFAULT 'REQUEST_ACCESS',
    status                                         STRING NOT NULL DEFAULT 'DRAFT',
    effective_from                                  DATE NOT NULL,
    effective_to                                     DATE,
    version                                            INT NOT NULL DEFAULT 1,
    created_at                                          TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_at                                           TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_by                                            STRING
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Approved relationships between concepts, including the only join paths the compiler is allowed to use.';

ALTER TABLE ${catalog}.ontology.relationship ADD CONSTRAINT pk_relationship PRIMARY KEY (relationship_id, version);
ALTER TABLE ${catalog}.ontology.relationship ADD CONSTRAINT fk_relationship_source FOREIGN KEY (source_concept_id) REFERENCES ${catalog}.ontology.concept (concept_id);
ALTER TABLE ${catalog}.ontology.relationship ADD CONSTRAINT fk_relationship_target FOREIGN KEY (target_concept_id) REFERENCES ${catalog}.ontology.concept (concept_id);
