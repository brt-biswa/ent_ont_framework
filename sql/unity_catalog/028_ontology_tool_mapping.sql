CREATE TABLE IF NOT EXISTS ${catalog}.ontology.tool_mapping (
    tool_mapping_id     STRING NOT NULL,
    tool_name              STRING NOT NULL,
    mcp_service_ref            STRING NOT NULL,
    concept_ids                    ARRAY<STRING>,
    input_schema_ref                  STRING,
    output_schema_ref                    STRING,
    created_at                              TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_at                                 TIMESTAMP NOT NULL DEFAULT current_timestamp()
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Registered MCP tools and the concepts each one is allowed to touch — narrow, typed tool selection (Sec. 11).';

ALTER TABLE ${catalog}.ontology.tool_mapping ADD CONSTRAINT pk_tool_mapping PRIMARY KEY (tool_mapping_id);
