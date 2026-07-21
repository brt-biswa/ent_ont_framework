CREATE TABLE IF NOT EXISTS ${catalog}.ontology.domain_registry (
    domain                       STRING NOT NULL,
    description                     STRING NOT NULL,
    steward                            STRING NOT NULL,
    council_reviewed                      BOOLEAN NOT NULL DEFAULT FALSE,
    shared_concepts_referenced               ARRAY<STRING>,
    created_at                                  TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_at                                     TIMESTAMP NOT NULL DEFAULT current_timestamp()
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Bounded-domain ontology registry (Sec. 7) — each row is one domain team onboarded onto the framework.';

ALTER TABLE ${catalog}.ontology.domain_registry ADD CONSTRAINT pk_domain_registry PRIMARY KEY (domain);
