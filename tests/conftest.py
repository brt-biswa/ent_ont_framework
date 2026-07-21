"""Shared pytest fixtures. No live Databricks/Lakebase connection is needed
for these tests — every fixture builds framework objects directly against
in-memory fakes or the pure-Python pieces (compiler, validator, policy
gateway) that don't require a network call.
"""
from __future__ import annotations

import datetime as dt

import pytest

from enterprise_ontology.models import (
    Concept, MetricDefinition, DimensionDefinition, OntologyContext, UserContext,
    ConceptType, AuthorityLevel, TimeGrain, Operator, ValueResolutionStrategy,
)


@pytest.fixture
def today() -> dt.date:
    return dt.date(2026, 7, 22)


@pytest.fixture
def user_context() -> UserContext:
    return UserContext(
        principal_id="jane.doe@yourco.com",
        entitlement_group_ids=["finance-analysts"],
        environment="test",
    )


@pytest.fixture
def net_revenue_concept(today) -> Concept:
    return Concept(
        concept_id="METRIC.NET_REVENUE",
        canonical_name="Net Revenue",
        concept_type=ConceptType.MEASURE,
        definition="Gross revenue less returns, allowances and discounts.",
        domain="finance",
        owner="finance-data-eng@yourco.com",
        authority_level=AuthorityLevel.CERTIFIED_METRIC_VIEW_OR_FUNCTION,
        effective_from=today,
        status="ACTIVE",
        # OPEN here so semantic-validator/compiler tests exercise plan shape,
        # not authorization — REQUEST_ACCESS/HIDDEN fail-closed behavior is
        # covered exhaustively in test_authz.py instead.
        discoverability="OPEN",
    )


@pytest.fixture
def net_revenue_metric(today) -> MetricDefinition:
    return MetricDefinition(
        metric_id="METRIC.NET_REVENUE",
        concept_id="METRIC.NET_REVENUE",
        business_definition="Gross revenue less returns, allowances and discounts.",
        formula="gross_revenue - returns - allowances - discounts",
        aggregation_behavior="SUM",
        allowed_dimension_ids=["ORG.OPERATING_UNIT"],
        time_grain=TimeGrain.MONTH,
        certified_source_asset="enterprise_ontology.finance_gold.net_revenue_mv",
        is_certified=True,
        owner="finance-data-eng@yourco.com",
        effective_from=today,
        status="ACTIVE",
    )


@pytest.fixture
def operating_unit_dimension(today) -> DimensionDefinition:
    return DimensionDefinition(
        dimension_id="ORG.OPERATING_UNIT",
        concept_id="ORG.OPERATING_UNIT",
        key_column="operating_unit_id",
        label_column="operating_unit_name",
        allowed_operators=[Operator.EQUALS, Operator.IN],
        value_resolution_strategy=ValueResolutionStrategy.EXACT_MATCH,
        owner="finance-data-eng@yourco.com",
        effective_from=today,
        status="ACTIVE",
    )


@pytest.fixture
def ontology_context(net_revenue_concept, net_revenue_metric, operating_unit_dimension) -> OntologyContext:
    return OntologyContext(
        ontology_version="2026.07.1",
        policy_version="1.0.0",
        matched_concepts=[net_revenue_concept],
        approved_metrics=[net_revenue_metric],
        approved_dimensions=[operating_unit_dimension],
        approved_sources=["enterprise_ontology.finance_gold.net_revenue_mv"],
    )
