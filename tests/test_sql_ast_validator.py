"""Tests for sql_policy/ast_validator.py — the last line of defense before
any query reaches a warehouse (PRD Sec. 14, 16)."""
import pytest

from enterprise_ontology.sql_policy.ast_validator import SQLPolicyGateway
from enterprise_ontology.sql_policy.policy_config import DEFAULT_POLICY


@pytest.fixture
def gateway() -> SQLPolicyGateway:
    return SQLPolicyGateway(
        DEFAULT_POLICY,
        approved_assets=frozenset({"enterprise_ontology.finance_gold.net_revenue_mv", "a", "b"}),
    )


def test_certified_select_passes(gateway):
    sql = """SELECT operating_unit, SUM(net_revenue) AS total_revenue
             FROM enterprise_ontology.finance_gold.net_revenue_mv
             WHERE fiscal_period = '2026-Q2' GROUP BY operating_unit LIMIT 100"""
    result = gateway.validate(sql)
    assert result.passed, result.denied_reasons


def test_select_star_is_denied(gateway):
    result = gateway.validate("SELECT * FROM enterprise_ontology.finance_gold.net_revenue_mv LIMIT 10")
    assert not result.passed
    assert any("SELECT *" in r for r in result.denied_reasons)


@pytest.mark.parametrize("statement", [
    "DROP TABLE enterprise_ontology.finance_gold.net_revenue_mv",
    "INSERT INTO enterprise_ontology.finance_gold.net_revenue_mv VALUES (1,2,3)",
    "UPDATE enterprise_ontology.finance_gold.net_revenue_mv SET net_revenue = 0",
    "DELETE FROM enterprise_ontology.finance_gold.net_revenue_mv",
    "GRANT SELECT ON enterprise_ontology.finance_gold.net_revenue_mv TO `all`",
])
def test_ddl_dml_grant_statements_are_denied(gateway, statement):
    result = gateway.validate(statement)
    assert not result.passed


@pytest.mark.parametrize("statement", [
    "SELECT a.x FROM a, b LIMIT 10",             # implicit comma-join
    "SELECT a.x FROM a JOIN b LIMIT 10",          # explicit JOIN, no ON
    "SELECT a.x FROM a CROSS JOIN b LIMIT 10",    # explicit CROSS JOIN
])
def test_cartesian_joins_are_denied(gateway, statement):
    result = gateway.validate(statement)
    assert not result.passed
    assert any("Cartesian" in r for r in result.denied_reasons)


def test_proper_join_with_on_clause_passes(gateway):
    result = gateway.validate("SELECT a.x FROM a JOIN b ON a.id = b.id LIMIT 10")
    assert result.passed, result.denied_reasons


def test_cte_alias_is_not_checked_against_approved_assets(gateway):
    sql = """WITH base AS (
                SELECT operating_unit, net_revenue
                FROM enterprise_ontology.finance_gold.net_revenue_mv WHERE net_revenue > 0
             )
             SELECT operating_unit, SUM(net_revenue) FROM base GROUP BY operating_unit LIMIT 50"""
    result = gateway.validate(sql)
    assert result.passed, result.denied_reasons


def test_missing_limit_is_denied(gateway):
    sql = "SELECT operating_unit FROM enterprise_ontology.finance_gold.net_revenue_mv"
    result = gateway.validate(sql)
    assert not result.passed
    assert any("LIMIT" in r for r in result.denied_reasons)


def test_limit_exceeding_max_rows_is_denied(gateway):
    sql = "SELECT operating_unit FROM enterprise_ontology.finance_gold.net_revenue_mv LIMIT 999999"
    result = gateway.validate(sql)
    assert not result.passed
    assert any("exceeds max_rows" in r for r in result.denied_reasons)


def test_unapproved_table_is_denied(gateway):
    sql = "SELECT x FROM some_random_table LIMIT 10"
    result = gateway.validate(sql)
    assert not result.passed
    assert any("Unapproved table" in r for r in result.denied_reasons)


def test_external_url_literal_is_denied(gateway):
    sql = "SELECT 'https://evil.example.com' AS x FROM enterprise_ontology.finance_gold.net_revenue_mv LIMIT 10"
    result = gateway.validate(sql)
    assert not result.passed


def test_unparseable_sql_fails_closed(gateway):
    result = gateway.validate("SELECT FROM WHERE ###not valid sql###")
    assert not result.passed
    assert result.denied_reasons
