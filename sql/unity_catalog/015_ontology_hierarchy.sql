CREATE TABLE IF NOT EXISTS ${catalog}.ontology.hierarchy (
    hierarchy_id     STRING NOT NULL,
    concept_id          STRING NOT NULL,
    name                   STRING NOT NULL,
    max_depth                 INT,
    owner                        STRING NOT NULL,
    status                          STRING NOT NULL DEFAULT 'DRAFT',
    effective_from                    DATE NOT NULL,
    effective_to                        DATE,
    version                                INT NOT NULL DEFAULT 1,
    created_at                              TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_at                                TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_by                                  STRING
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Named hierarchies (e.g. sales hierarchy, product hierarchy, org hierarchy).';

ALTER TABLE ${catalog}.ontology.hierarchy ADD CONSTRAINT pk_hierarchy PRIMARY KEY (hierarchy_id, version);
ALTER TABLE ${catalog}.ontology.hierarchy ADD CONSTRAINT fk_hierarchy_concept FOREIGN KEY (concept_id) REFERENCES ${catalog}.ontology.concept (concept_id);
