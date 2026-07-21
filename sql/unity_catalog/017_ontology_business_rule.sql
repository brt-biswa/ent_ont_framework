CREATE TABLE IF NOT EXISTS ${catalog}.ontology.business_rule (
    rule_id                STRING NOT NULL,
    concept_id                 STRING NOT NULL,
    rule_type                     STRING NOT NULL COMMENT 'DEFINITION|CALCULATION|VALIDATION|ELIGIBILITY|SECURITY|TEMPORAL|AGGREGATION|APPROVAL|EXCEPTION|COMPARISON|MATERIALITY',
    description                      STRING NOT NULL,
    executable_reference                 STRING COMMENT 'Metric view / certified view / UC function / DQ rule implementing this rule',
    owner                                    STRING NOT NULL,
    status                                      STRING NOT NULL DEFAULT 'DRAFT',
    effective_from                                DATE NOT NULL,
    effective_to                                     DATE,
    version                                            INT NOT NULL DEFAULT 1,
    created_at                                           TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_at                                             TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_by                                               STRING
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Business rules linked to executable assets — critical rules must not exist only in prompts.';

ALTER TABLE ${catalog}.ontology.business_rule ADD CONSTRAINT pk_business_rule PRIMARY KEY (rule_id, version);
ALTER TABLE ${catalog}.ontology.business_rule ADD CONSTRAINT fk_business_rule_concept FOREIGN KEY (concept_id) REFERENCES ${catalog}.ontology.concept (concept_id);
