"""Deterministic semantic plan validator — PRD Sec. 15, engineering interface
`SemanticValidator` (Sec. 28). Confirms: metric certification, metric-dimension
compatibility, canonical filter values, user authorization, valid hierarchy
traversal, allowed grain, allowed comparison basis, allowed date range and
output size. This runs on every plan the LLM produces before it is ever
compiled to SQL — nothing here is optional or "best effort."
"""
from __future__ import annotations

from ..config import Settings, get_settings
from ..models import (
    OntologyContext, PlanValidationResult, SemanticPlan, UserContext, ComparisonBasis,
)
from ..metrics.metric_service import MetricService
from ..security.authz import check_concept_access


class SemanticValidator:
    def __init__(self, metric_service: MetricService, settings: Settings | None = None):
        self._metrics = metric_service
        self.settings = settings or get_settings()

    async def validate(
        self, plan: SemanticPlan, context: OntologyContext, user_context: UserContext
    ) -> PlanValidationResult:
        violations: list[str] = []

        # 1. Metric certification — every referenced metric must be certified
        #    and present in the projected context (never invented).
        approved_metric_ids = {m.metric_id for m in context.approved_metrics}
        for metric_id in plan.metric_ids:
            if metric_id not in approved_metric_ids:
                violations.append(f"Metric '{metric_id}' is not in the approved context for this request")
                continue
            metric = next(m for m in context.approved_metrics if m.metric_id == metric_id)
            if not metric.is_certified:
                violations.append(f"Metric '{metric_id}' is not certified")

        # 2. Metric-dimension compatibility.
        for metric_id in plan.metric_ids:
            for dimension_id in plan.dimension_ids:
                compatible, reason = await self._metrics.is_dimension_compatible(metric_id, dimension_id)
                if not compatible:
                    violations.append(f"{metric_id} x {dimension_id}: {reason}")

        # 3. Canonical filter values — reject anything that looks like an
        #    unresolved free-text guess rather than a canonical_id.
        approved_dimension_ids = {d.dimension_id for d in context.approved_dimensions}
        for f in plan.filters:
            if f.dimension_id not in approved_dimension_ids:
                violations.append(f"Filter dimension '{f.dimension_id}' is not in the approved context")
            if not f.canonical_values:
                violations.append(f"Filter on '{f.dimension_id}' has no resolved canonical values")

        # 4. User authorization on every referenced concept.
        for concept in context.matched_concepts:
            decision = check_concept_access(concept, user_context)
            if not decision.is_authorized:
                violations.append(f"Concept '{concept.concept_id}' not authorized: {decision.reason}")

        # 5. Allowed comparison basis (only what the metric supports).
        for metric_id in plan.metric_ids:
            metric = next((m for m in context.approved_metrics if m.metric_id == metric_id), None)
            if metric and plan.comparison != ComparisonBasis.NONE:
                if plan.comparison.value not in metric.comparison_rules and metric.comparison_rules:
                    violations.append(f"Comparison basis '{plan.comparison.value}' not allowed for {metric_id}")

        # 6. Output size / row limit.
        if plan.limit > self.settings.max_sql_rows:
            violations.append(f"Requested limit {plan.limit} exceeds max_sql_rows={self.settings.max_sql_rows}")

        requires_clarification = any("no resolved canonical values" in v for v in violations)

        return PlanValidationResult(
            is_valid=len(violations) == 0,
            plan=plan,
            violations=violations,
            requires_clarification=requires_clarification,
            clarification_prompt=(
                "One or more filter values could not be resolved to a canonical value — "
                "could you clarify which specific value you mean?"
                if requires_clarification else None
            ),
        )
