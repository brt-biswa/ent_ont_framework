"""Central configuration. All values come from environment variables so the
same wheel/app deploys unmodified across dev/staging/prod (Databricks Apps
inject these via `app.yaml` env blocks; jobs inject them via bundle variables).

Never put secrets (tokens, passwords) in source control. Databricks Apps
resolve `valueFrom` secret references at deploy time; asyncpg/Lakebase
credentials should come from a Databricks-managed OAuth token, not a static
password, wherever Lakebase supports it.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pydantic import BaseModel


class Settings(BaseModel):
    # Unity Catalog
    databricks_host: str = os.environ.get("DATABRICKS_HOST", "")
    databricks_token: str = os.environ.get("DATABRICKS_TOKEN", "")
    warehouse_http_path: str = os.environ.get("DATABRICKS_WAREHOUSE_HTTP_PATH", "")
    ontology_catalog: str = os.environ.get("ONTOLOGY_CATALOG", "enterprise_ontology")

    # Lakebase (managed Postgres) — operational / L2-cache state
    lakebase_host: str = os.environ.get("LAKEBASE_HOST", "")
    lakebase_port: int = int(os.environ.get("LAKEBASE_PORT", "5432"))
    lakebase_database: str = os.environ.get("LAKEBASE_DATABASE", "ontology_state")
    lakebase_user: str = os.environ.get("LAKEBASE_USER", "")
    lakebase_password: str = os.environ.get("LAKEBASE_PASSWORD", "")  # prefer OAuth token below
    lakebase_oauth_token: str = os.environ.get("LAKEBASE_OAUTH_TOKEN", "")
    lakebase_sslmode: str = os.environ.get("LAKEBASE_SSLMODE", "require")
    lakebase_pool_min_size: int = int(os.environ.get("LAKEBASE_POOL_MIN", "2"))
    lakebase_pool_max_size: int = int(os.environ.get("LAKEBASE_POOL_MAX", "10"))

    # Policy / governance
    sql_policy_version: str = os.environ.get("SQL_POLICY_VERSION", "1.0.0")
    max_sql_tables: int = int(os.environ.get("SQL_POLICY_MAX_TABLES", "6"))
    max_sql_rows: int = int(os.environ.get("SQL_POLICY_MAX_ROWS", "10000"))
    max_sql_date_range_days: int = int(os.environ.get("SQL_POLICY_MAX_DATE_RANGE_DAYS", "1100"))
    sql_query_timeout_seconds: int = int(os.environ.get("SQL_POLICY_TIMEOUT_SECONDS", "30"))

    # Caching
    l1_cache_max_items: int = int(os.environ.get("L1_CACHE_MAX_ITEMS", "5000"))
    l1_cache_ttl_seconds: int = int(os.environ.get("L1_CACHE_TTL_SECONDS", "300"))
    l2_cache_ttl_seconds: int = int(os.environ.get("L2_CACHE_TTL_SECONDS", "1800"))

    # LLM / model serving endpoint used by the semantic planner
    planner_model_endpoint: str = os.environ.get("PLANNER_MODEL_ENDPOINT", "databricks-claude-sonnet")

    environment: str = os.environ.get("ENVIRONMENT", "dev")


@lru_cache
def get_settings() -> Settings:
    return Settings()
