CREATE TABLE IF NOT EXISTS ${catalog}.ontology.version (
    version_id       STRING NOT NULL,
    label                STRING NOT NULL COMMENT 'e.g. 2026.07.1',
    is_active               BOOLEAN NOT NULL DEFAULT FALSE,
    activated_at               TIMESTAMP,
    activated_by                  STRING,
    notes                            STRING,
    created_at                         TIMESTAMP NOT NULL DEFAULT current_timestamp()
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Ontology version history. Exactly one row should have is_active=true at a time; enforced by the activation job, not a DB constraint (Delta has no partial unique index).';

ALTER TABLE ${catalog}.ontology.version ADD CONSTRAINT pk_version PRIMARY KEY (version_id);
