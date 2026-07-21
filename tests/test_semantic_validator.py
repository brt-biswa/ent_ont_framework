"""Tests for planner/semantic_validator.py — PRD Sec. 15."""
import pytest

from enterprise_ontology.planner.semantic_validator import SemanticValidator
from enterprise_ontology.metrics.metric_service import MetricService
from enterprise_ontology.models import SemanticPlan, PlanFilter, Operator, Discoverability


class _FakeRepo:
    """Minimal stand-in for UnityCatalogOntologyRepository._query, scoped to
    only what MetricService.get()/is_dimension_compatible() need."""

    def __init__(self, metric_row: dict):
        self._metric_row = metric_row

    def _query(self, sql_text, params=()):  # noqa: D401 — mimics repo signature
        return [self._metric_row]


@pytest.fixture
def metric_service(net_revenue_metric):
    row = net_revenue_metric.model_dump(mode="json")
    return MetricService(_FakeRepo(row))


@pytest.mark.asyncio
async def test_valid_plan_passes(ontology_context, user_context, metric_service):
    plan = SemanticPlan(
        metric_ids=["METRIC.NET_REVENUE"],
        dimension_ids=["ORG.OPERATING_UNIT"],
        filters=[PlanFilter(dimension_id="ORG.OPERATING_UNIT", operator=Operator.EQUALS, canonical_values=["OU-1"])],
        limit=100,
    )
    validator = SemanticValidator(metric_service)
    result = await validator.validate(plan, ontology_context, user_context)
    assert result.is_valid, result.violations


@pytest.mark.asyncio
async def test_unresolved_filter_value_triggers_clarification(ontology_context, user_context, metric_service):
    plan = SemanticPlan(
        metric_ids=["METRIC.NET_REVENUE"],
        dimension_ids=["ORG.OPERATING_UNIT"],
        filters=[PlanFilter(dimension_id="ORG.OPERATING_UNIT", operator=Operator.EQUALS, canonical_values=[])],
        limit=100,
    )
    validator = SemanticValidator(metric_service)
    result = await validator.validate(plan, ontology_context, user_context)
    assert not result.is_valid
    assert result.requires_clarification


@pytest.mark.asyncio
async def test_metric_not_in_context_is_rejected(ontology_context, user_context, metric_service):
    plan = SemanticPlan(metric_ids=["METRIC.NOT_APPROVED"], dimension_ids=[], limit=100)
    validator = SemanticValidator(metric_service)
    result = await validator.validate(plan, ontology_context, user_context)
    assert not result.is_valid
    assert any("not in the approved context" in v for v in result.violations)


@pytest.mark.asyncio
async def test_row_limit_over_max_is_rejected(ontology_context, user_context, metric_service):
    plan = SemanticPlan(metric_ids=["METRIC.NET_REVENUE"], dimension_ids=[], limit=100)
    plan.limit = 50_000
    validator = SemanticValidator(metric_service)
    result = await validator.validate(plan, ontology_context, user_context)
    assert not result.is_valid
    assert any("exceeds max_sql_rows" in v for v in result.violations)


@pytest.mark.asyncio
async def test_hidden_concept_is_never_authorized(ontology_context, user_context, metric_service, net_revenue_concept):
    net_revenue_concept.discoverability = Discoverability.HIDDEN
    ontology_context.matched_concepts = [net_revenue_concept]
    plan = SemanticPlan(metric_ids=["METRIC.NET_REVENUE"], dimension_ids=[], limit=10)
    validator = SemanticValidator(metric_service)
    result = await validator.validate(plan, ontology_context, user_context)
    assert not result.is_valid
    assert any("not authorized" in v for v in result.violations)
