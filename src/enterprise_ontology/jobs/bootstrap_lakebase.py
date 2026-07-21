"""Applies sql/lakebase/*.sql in order against the Lakebase (Postgres-compatible)
instance. This is the application-database bootstrap: creates the
`ontology_state` and `audit` schemas and every operational table the
framework depends on at runtime.

Invoked by the `create_lakebase_tables` task in databricks.yml
(`python_wheel_task` -> entry point `bootstrap_lakebase`), or standalone:

    python -m enterprise_ontology.jobs.bootstrap_lakebase --instance ontology-state
"""
from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

import asyncpg

from ..config import get_settings
from ._sql_runner import run_sql_directory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SQL_DIR = Path(__file__).resolve().parents[3] / "sql" / "lakebase"


async def _run() -> None:
    settings = get_settings()
    password = settings.lakebase_oauth_token or settings.lakebase_password

    conn = await asyncpg.connect(
        host=settings.lakebase_host,
        port=settings.lakebase_port,
        database=settings.lakebase_database,
        user=settings.lakebase_user,
        password=password,
        ssl=settings.lakebase_sslmode != "disable",
    )
    try:
        # asyncpg is async end-to-end; run_sql_directory's execute_fn callback
        # is synchronous, so collect statements first and await them here.
        statements: list[str] = []
        run_sql_directory(SQL_DIR, {}, statements.append)  # Lakebase DDL has no ${var} substitution today
        for statement in statements:
            logger.info("EXEC: %s", statement.splitlines()[0][:120])
            await conn.execute(statement)
    finally:
        await conn.close()

    logger.info(
        "Lakebase bootstrapped: schemas ontology_state, audit created in database=%s",
        settings.lakebase_database,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", default=None, help="Lakebase instance name (informational/logging only)")
    args = parser.parse_args()
    if args.instance:
        logger.info("Bootstrapping Lakebase instance=%s", args.instance)
    asyncio.run(_run())


if __name__ == "__main__":
    main()
