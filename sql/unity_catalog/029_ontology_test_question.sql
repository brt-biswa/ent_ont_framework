CREATE TABLE IF NOT EXISTS ${catalog}.ontology.test_question (
    test_question_id        STRING NOT NULL,
    domain                      STRING NOT NULL,
    question_text                   STRING NOT NULL,
    expected_concept_ids                ARRAY<STRING>,
    expected_metric_ids                    ARRAY<STRING>,
    expected_dimension_ids                    ARRAY<STRING>,
    expected_plan                                STRING COMMENT 'JSON-encoded expected SemanticPlan for exact-match evaluation',
    category                                        STRING NOT NULL DEFAULT 'GENERAL' COMMENT 'CONCEPT_RESOLUTION|SYNONYM|NON_EQUIVALENCE|AMBIGUITY|METRIC_SELECTION|DIMENSION_SELECTION|ENTITY_RESOLUTION|JOIN_PATH|FISCAL_PERIOD|AUTHORIZATION|SEMANTIC_PLANNING|SQL_COMPILATION|CONSISTENCY|HISTORICAL_VERSION|DEPRECATED_SOURCE',
    created_at                                          TIMESTAMP NOT NULL DEFAULT current_timestamp()
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Gold evaluation dataset (Sec. 24). Grows with every onboarded domain — 100 gold questions is the Phase 1 exit bar.';

ALTER TABLE ${catalog}.ontology.test_question ADD CONSTRAINT pk_test_question PRIMARY KEY (test_question_id);
