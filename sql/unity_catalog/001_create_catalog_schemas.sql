-- =============================================================================
-- Unity Catalog bootstrap for the Enterprise Ontology Framework.
--
-- Creates the catalog + two schemas:
--   ontology  -- the governed registry (system of record for meaning)
--   audit     -- immutable, long-retention audit trail (Delta system tables
--                pattern; append-only, never updated in place)
--
-- ${catalog} is substituted by the Databricks Asset Bundle variable
-- var.ontology_catalog at deploy time (see databricks.yml).
-- =============================================================================

CREATE CATALOG IF NOT EXISTS ${catalog}
    COMMENT 'Enterprise Ontology Framework for Agentic AI — governed meaning layer';

CREATE SCHEMA IF NOT EXISTS ${catalog}.ontology
    COMMENT 'Ontology registry: concepts, relationships, metrics, dimensions, rules, mappings, governance';

CREATE SCHEMA IF NOT EXISTS ${catalog}.audit
    COMMENT 'Immutable, append-only audit trail. Long-term system of record (also mirrored to Lakebase for fast reads).';

-- Base RBAC: platform team owns DDL; domain stewards get MODIFY on ontology
-- registry tables ONLY through the change-request workflow (never direct DML
-- from agents). Grant patterns below are illustrative — bind to real account
-- groups at deploy time.
GRANT USE CATALOG ON CATALOG ${catalog} TO `account users`;
GRANT USE SCHEMA ON SCHEMA ${catalog}.ontology TO `account users`;
GRANT SELECT ON SCHEMA ${catalog}.ontology TO `account users`;
GRANT USE SCHEMA ON SCHEMA ${catalog}.audit TO `ontology-platform-team`;
GRANT SELECT ON SCHEMA ${catalog}.audit TO `ontology-platform-team`;
GRANT MODIFY ON SCHEMA ${catalog}.ontology TO `ontology-platform-team`;
