-- =============================================================================
-- ontology.hierarchy_node — PRD Sec. 13. Each node carries its FULL materialized
-- path so hierarchy expansion (expand_hierarchy MCP tool) is a single filtered
-- scan rather than a recursive join at request time.
-- =============================================================================
CREATE TABLE IF NOT EXISTS ${catalog}.ontology.hierarchy_node (
    node_id           STRING NOT NULL,
    hierarchy_id         STRING NOT NULL,
    parent_node_id           STRING,
    canonical_id                STRING NOT NULL COMMENT 'e.g. SH-EMEA-ENTERPRISE',
    display_name                    STRING NOT NULL,
    path                                ARRAY<STRING> NOT NULL COMMENT "e.g. ['Global Sales','EMEA','Enterprise']",
    level                                  INT NOT NULL DEFAULT 0,
    owner                                      STRING NOT NULL,
    status                                        STRING NOT NULL DEFAULT 'DRAFT',
    effective_from                                  DATE NOT NULL,
    effective_to                                       DATE,
    version                                              INT NOT NULL DEFAULT 1,
    created_at                                             TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_at                                               TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_by                                                 STRING
)
USING DELTA
PARTITIONED BY (hierarchy_id)
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Materialized-path hierarchy nodes for fast expansion/lookup without recursive joins.';

ALTER TABLE ${catalog}.ontology.hierarchy_node ADD CONSTRAINT pk_hierarchy_node PRIMARY KEY (node_id, version);
ALTER TABLE ${catalog}.ontology.hierarchy_node ADD CONSTRAINT fk_hierarchy_node_hierarchy FOREIGN KEY (hierarchy_id) REFERENCES ${catalog}.ontology.hierarchy (hierarchy_id);

OPTIMIZE ${catalog}.ontology.hierarchy_node ZORDER BY (canonical_id);
