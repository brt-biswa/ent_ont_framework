CREATE TABLE IF NOT EXISTS ${catalog}.ontology.document_mapping (
    document_mapping_id     STRING NOT NULL,
    concept_ids                 ARRAY<STRING> NOT NULL,
    document_id                    STRING NOT NULL,
    title                              STRING NOT NULL,
    section                              STRING,
    page                                    INT,
    jurisdiction                              STRING,
    domain                                       STRING,
    approval_state                                  STRING NOT NULL DEFAULT 'DRAFT',
    superseded_by_document_id                          STRING,
    source_uri                                            STRING,
    owner                                                    STRING NOT NULL,
    status                                                      STRING NOT NULL DEFAULT 'DRAFT',
    effective_from                                                DATE NOT NULL,
    effective_to                                                    DATE,
    version                                                           INT NOT NULL DEFAULT 1,
    created_at                                                          TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_at                                                            TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_by                                                              STRING
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'AI Search chunk-level metadata mapping documents back to concepts (Sec. 18).';

ALTER TABLE ${catalog}.ontology.document_mapping ADD CONSTRAINT pk_document_mapping PRIMARY KEY (document_mapping_id, version);
