"""Constrained LLM SQL generation — PRD Sec. 16 "where deterministic
compilation cannot support the use case, the LLM may generate candidate SQL
using only approved assets, fields, joins, values and parameters."

This is a FALLBACK, only invoked when DeterministicCompiler.compile() returns
None. Its output is NEVER trusted directly — every generated statement must
pass sql_policy.ast_validator.SQLPolicyGateway before execution (PRD Sec. 14
Level 2). This class does not execute anything; it only proposes candidate SQL.
"""
from __future__ import annotations

import logging

from ..config import Settings, get_settings
from ..models import OntologyContext, SemanticPlan

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You generate a single read-only SQL SELECT statement using ONLY the \
tables/views, columns and join expressions explicitly listed below. You are FORBIDDEN from:
- referencing any table, view, column, or function not listed
- inventing a join not listed under "approved_joins"
- using SELECT *
- using INSERT/UPDATE/DELETE/MERGE/CREATE/ALTER/DROP/TRUNCATE/GRANT/REVOKE
- using dynamic SQL, external URLs, or unbounded result sets

Return ONLY the SQL statement, no prose, no markdown fences, no explanation."""


class ConstrainedSQLGenerator:
    def __init__(self, settings: Settings | None = None, model_client=None):
        self.settings = settings or get_settings()
        self._model_client = model_client

    async def generate(self, plan: SemanticPlan, context: OntologyContext) -> str:
        approved_assets = sorted(set(context.approved_sources))
        approved_joins = [
            r.approved_join_ref for r in context.relevant_relationships if r.approved_join_ref
        ]

        user_prompt = (
            f"Semantic plan:\n{plan.model_dump_json(indent=2)}\n\n"
            f"approved_assets = {approved_assets}\n"
            f"approved_joins = {approved_joins}\n"
            f"max_rows = {self.settings.max_sql_rows}\n"
            f"max_tables = {self.settings.max_sql_tables}\n"
        )

        raw_sql = await self._call_model(_SYSTEM_PROMPT, user_prompt)
        cleaned = raw_sql.strip().strip("`")
        if cleaned.lower().startswith("sql"):
            cleaned = cleaned[3:].strip()
        logger.info("Constrained LLM SQL generation produced %d chars", len(cleaned))
        return cleaned

    async def _call_model(self, system_prompt: str, user_prompt: str) -> str:
        if self._model_client is not None:
            return await self._model_client(system_prompt, user_prompt)

        from databricks.sdk import WorkspaceClient

        client = WorkspaceClient()
        response = client.serving_endpoints.query(
            name=self.settings.planner_model_endpoint,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,
            max_tokens=1024,
        )
        return response.choices[0].message.content
