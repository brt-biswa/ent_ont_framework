"""Applies sql/unity_catalog/*.sql in order against the configured SQL
warehouse. Invoked by the `create_ontology_registry_tables` task in
databricks.yml, or standalone: `python -m enterprise_ontology.jobs.bootstrap_uc`.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from databricks import sql as databricks_sql

from ..config import get_settings
from ._sql_runner import run_sql_directory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SQL_DIR = Path(__file__).resolve().parents[3] / "sql" / "unity_catalog"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default=None, help="Overrides ONTOLOGY_CATALOG env var")
    args = parser.parse_args()

    settings = get_settings()
    catalog = args.catalog or settings.ontology_catalog

    with databricks_sql.connect(
        server_hostname=settings.databricks_host,
        http_path=settings.warehouse_http_path,
        access_token=settings.databricks_token,
    ) as conn:
        with conn.cursor() as cur:
            def execute(statement: str) -> None:
                logger.debug("EXEC: %s", statement[:200])
                cur.execute(statement)

            run_sql_directory(SQL_DIR, {"catalog": catalog}, execute)

    logger.info("Unity Catalog ontology + audit schemas bootstrapped in catalog=%s", catalog)


if __name__ == "__main__":
    main()
