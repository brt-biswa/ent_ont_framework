CREATE TABLE IF NOT EXISTS ${catalog}.ontology.agent_mapping (
    agent_mapping_id      STRING NOT NULL,
    agent_name                STRING NOT NULL,
    domain                       STRING NOT NULL,
    genie_agent_ref                 STRING,
    allowed_concept_ids                ARRAY<STRING>,
    allowed_metric_ids                    ARRAY<STRING>,
    max_sql_policy_level                     INT NOT NULL DEFAULT 2 COMMENT '1=certified deterministic only, 2=governed exploratory allowed',
    created_at                                  TIMESTAMP NOT NULL DEFAULT current_timestamp(),
    updated_at                                     TIMESTAMP NOT NULL DEFAULT current_timestamp()
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Which concepts/metrics a given agent is scoped to — bounded domain agents, never one enterprise-wide agent (Sec. 17 anti-pattern).';

ALTER TABLE ${catalog}.ontology.agent_mapping ADD CONSTRAINT pk_agent_mapping PRIMARY KEY (agent_mapping_id);
ALTER TABLE ${catalog}.ontology.agent_mapping ADD CONSTRAINT fk_agent_mapping_domain FOREIGN KEY (domain) REFERENCES ${catalog}.ontology.domain_registry (domain);
