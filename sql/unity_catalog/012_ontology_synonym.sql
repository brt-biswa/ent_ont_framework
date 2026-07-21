-- =============================================================================
-- ontology.synonym — PRD Sec. 6.5. Includes PROHIBITED_EQUIVALENCE rows so
-- the resolver can actively reject near-miss terms, not just fail to match.
-- =============================================================================
CREATE TABLE IF NOT EXISTS ${catalog}.ontology.synonym (
    synonym_id       STRING NOT NULL,
    concept_id         STRING NOT NULL,
    term                  STRING NOT NULL,
    synonym_type            STRING NOT NULL COMMENT 'EXACT|CONTEXTUAL|ABBREVIATION|LEGACY|REGIONAL|MISSPELLING|PROHIBITED_EQUIVALENCE',
    locale                     STRING NOT NULL DEFAULT 'en-US',
    confidence                    DOUBLE NOT NULL DEFAULT 1.0,
    owner                            STRING NOT NULL,
    status                              STRING NOT NULL DEFAULT 'DRAFT',
    effective_from                       DATE NOT NULL,
    effective_to                          DATE,
    version                                 INT NOT NULL DEFAULT 1,
    created_at                               TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_at                                TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_by                                  STRING
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Synonyms, abbreviations and explicitly prohibited (non-)equivalences per concept.';

ALTER TABLE ${catalog}.ontology.synonym ADD CONSTRAINT pk_synonym PRIMARY KEY (synonym_id, version);
ALTER TABLE ${catalog}.ontology.synonym ADD CONSTRAINT fk_synonym_concept FOREIGN KEY (concept_id) REFERENCES ${catalog}.ontology.concept (concept_id);

-- Fast case-insensitive term lookup is done at query time via lower(term);
-- Delta does not support functional indexes, so the repository issues
-- lower(term) = ? predicates and relies on file-level Z-ordering below.
OPTIMIZE ${catalog}.ontology.synonym ZORDER BY (concept_id);
