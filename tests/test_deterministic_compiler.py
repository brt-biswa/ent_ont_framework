"""Tests for compiler/deterministic_compiler.py — PRD Sec. 16."""
import pytest

from enterprise_ontology.compiler.deterministic_compiler import DeterministicCompiler
from enterprise_ontology.models import SemanticPlan, PlanFilter, Operator


@pytest.mark.asyncio
async def test_compiles_simple_metric_by_dimension(ontology_context):
    plan = SemanticPlan(
        metric_ids=["METRIC.NET_REVENUE"],
        dimension_ids=["ORG.OPERATING_UNIT"],
        limit=100,
    )
    compiler = DeterministicCompiler()
    result = await compiler.compile(plan, ontology_context)

    assert result is not None
    assert result.used_deterministic_path
    assert "enterprise_ontology.finance_gold.net_revenue_mv" in result.sql
    assert "operating_unit_id" in result.sql
    assert "LIMIT 100" in result.sql
    assert result.assets_used == ["enterprise_ontology.finance_gold.net_revenue_mv"]


@pytest.mark.asyncio
async def test_returns_none_for_unknown_metric_falls_back(ontology_context):
    plan = SemanticPlan(metric_ids=["METRIC.DOES_NOT_EXIST"], dimension_ids=[], limit=100)
    compiler = DeterministicCompiler()
    result = await compiler.compile(plan, ontology_context)
    assert result is None  # caller should fall back to constrained LLM generation


@pytest.mark.asyncio
async def test_equals_filter_is_parameterized_not_inlined(ontology_context):
    plan = SemanticPlan(
        metric_ids=["METRIC.NET_REVENUE"],
        dimension_ids=["ORG.OPERATING_UNIT"],
        filters=[PlanFilter(dimension_id="ORG.OPERATING_UNIT", operator=Operator.EQUALS, canonical_values=["OU-042"])],
        limit=50,
    )
    compiler = DeterministicCompiler()
    result = await compiler.compile(plan, ontology_context)

    assert result is not None
    assert "OU-042" not in result.sql  # value must be parameterized, never inlined as a literal
    assert result.parameters.get("filter_0") == "OU-042"


@pytest.mark.asyncio
async def test_limit_is_capped_at_10000(ontology_context):
    plan = SemanticPlan(metric_ids=["METRIC.NET_REVENUE"], dimension_ids=[], limit=10)
    plan.limit = 999_999  # bypass pydantic validation to test the compiler's own defense in depth
    compiler = DeterministicCompiler()
    result = await compiler.compile(plan, ontology_context)
    assert result is not None
    assert "LIMIT 10000" in result.sql
