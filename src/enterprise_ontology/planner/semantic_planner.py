"""LLM semantic planner — PRD Sec. 12, 15, engineering interface `SemanticPlanner`
(Sec. 28). Calls a Databricks Foundation Model / Model Serving endpoint with
ONLY the small permission-aware OntologyContext for this question, and
demands a structured SemanticPlan back — never SQL, never prose (design
principle 7: "the LLM returns structured plans, not executable prose").

The actual model call goes through Databricks Model Serving so credentials
and endpoint routing stay inside the workspace boundary; swap
`_call_model` for any other Foundation-Model-API-compatible client without
touching the rest of this class.
"""
from __future__ import annotations

import json
import logging

from ..config import Settings, get_settings
from ..models import OntologyContext, SemanticPlan
from .prompts import SYSTEM_PROMPT, PLAN_OUTPUT_CONTRACT

logger = logging.getLogger(__name__)


class SemanticPlanner:
    def __init__(self, settings: Settings | None = None, model_client=None):
        self.settings = settings or get_settings()
        # `model_client` is injectable for testing; defaults to a lazy import
        # of the Databricks SDK's serving-endpoint client so unit tests that
        # never call `plan()` don't need workspace credentials configured.
        self._model_client = model_client

    async def plan(self, question: str, context: OntologyContext) -> SemanticPlan:
        core_context = self._build_core_context(context)
        user_prompt = (
            f"Question: {question}\n\n"
            f"Ontology context (ONLY these concepts/metrics/dimensions/filters exist for this request):\n"
            f"{json.dumps(core_context, indent=2)}\n\n"
            f"{PLAN_OUTPUT_CONTRACT}"
        )

        raw = await self._call_model(SYSTEM_PROMPT, user_prompt)
        plan_dict = self._safe_parse_json(raw)
        plan = SemanticPlan.model_validate(plan_dict)
        plan.ontology_version = context.ontology_version
        plan.raw_question = question
        return plan

    def _build_core_context(self, context: OntologyContext) -> dict:
        """A SMALL, relevant projection — never the full ontology (Sec. 12)."""
        return {
            "metrics": [
                {"metric_id": m.metric_id, "allowed_dimensions": m.allowed_dimension_ids, "time_grain": m.time_grain.value}
                for m in context.approved_metrics
            ],
            "dimensions": [
                {"dimension_id": d.dimension_id, "allowed_operators": [o.value for o in d.allowed_operators]}
                for d in context.approved_dimensions
            ],
            "ontology_version": context.ontology_version,
        }

    async def _call_model(self, system_prompt: str, user_prompt: str) -> str:
        if self._model_client is not None:
            return await self._model_client(system_prompt, user_prompt)

        # Default: Databricks Model Serving, OpenAI-compatible chat completions.
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

    @staticmethod
    def _safe_parse_json(raw: str) -> dict:
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            logger.error("Planner returned non-JSON output: %s", raw[:500])
            raise ValueError("Semantic planner did not return valid structured JSON") from exc
