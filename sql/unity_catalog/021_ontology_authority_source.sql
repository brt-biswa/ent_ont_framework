CREATE TABLE IF NOT EXISTS ${catalog}.ontology.authority_source (
    authority_source_id     STRING NOT NULL,
    concept_id                  STRING NOT NULL,
    authority_level                 STRING NOT NULL,
    source_reference                    STRING NOT NULL,
    confidence                             DOUBLE NOT NULL DEFAULT 1.0,
    approved_by                               STRING,
    review_date                                  DATE,
    owner                                            STRING NOT NULL,
    status                                              STRING NOT NULL DEFAULT 'DRAFT',
    effective_from                                        DATE NOT NULL,
    effective_to                                              DATE,
    version                                                     INT NOT NULL DEFAULT 1,
    created_at                                                    TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_at                                                      TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_by                                                        STRING
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Authority/provenance record per concept — every assertion traces to a ranked source (Sec. 6.7).';

ALTER TABLE ${catalog}.ontology.authority_source ADD CONSTRAINT pk_authority_source PRIMARY KEY (authority_source_id, version);
ALTER TABLE ${catalog}.ontology.authority_source ADD CONSTRAINT fk_authority_source_concept FOREIGN KEY (concept_id) REFERENCES ${catalog}.ontology.concept (concept_id);
