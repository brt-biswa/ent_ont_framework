"""SQL AST validator / policy gateway — PRD Sec. 14 ("governed SQL policy"),
Sec. 16 ("generated SQL must pass AST validation"), engineering interface
`SQLPolicyGateway` (Sec. 28).

This is the LAST line of defense before any compiler- or LLM-generated SQL
reaches a warehouse: it parses the statement with sqlglot, walks the AST (not
a regex/string search — string matching is trivially evaded by comments,
whitespace, or encoding tricks) and rejects anything outside the allow-list.

Design principle 19: authorization failures fail closed — any parse error,
any unrecognized construct, any ambiguity is a REJECT, never a "probably
fine, let it through."
"""
from __future__ import annotations

from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp

from .policy_config import SQLPolicyConfig, DEFAULT_POLICY


@dataclass
class PolicyValidationResult:
    passed: bool
    denied_reasons: list[str] = field(default_factory=list)
    tables_referenced: list[str] = field(default_factory=list)
    estimated_join_count: int = 0


class SQLPolicyGateway:
    """Level 2 governed exploratory analytics gate (PRD Sec. 14). Level 1
    (certified metric views / UC functions) never reaches this class at all
    — it is executed directly because it is already governed at the asset
    level. Level 3 (arbitrary SQL) is exactly what this class exists to
    prevent from ever running."""

    def __init__(self, config: SQLPolicyConfig = DEFAULT_POLICY, approved_assets: frozenset[str] = frozenset()):
        self.config = config
        self.approved_assets = approved_assets

    def validate(self, sql_text: str, dialect: str = "databricks") -> PolicyValidationResult:
        reasons: list[str] = []

        try:
            statements = sqlglot.parse(sql_text, read=dialect)
        except Exception as exc:  # noqa: BLE001 — any parse failure fails closed
            return PolicyValidationResult(passed=False, denied_reasons=[f"SQL failed to parse: {exc}"])

        if len(statements) != 1 or statements[0] is None:
            return PolicyValidationResult(passed=False, denied_reasons=["Exactly one statement is required"])

        tree = statements[0]

        reasons += self._check_statement_type(tree)
        reasons += self._check_denied_keywords(sql_text)
        reasons += self._check_select_star(tree)
        reasons += self._check_functions(tree)
        reasons += self._check_external_urls(tree)

        tables = self._extract_tables(tree)
        reasons += self._check_tables(tables)

        join_count = len(list(tree.find_all(exp.Join)))
        reasons += self._check_joins(tree, join_count)

        reasons += self._check_limit(tree)

        return PolicyValidationResult(
            passed=len(reasons) == 0,
            denied_reasons=reasons,
            tables_referenced=sorted(tables),
            estimated_join_count=join_count,
        )

    # ------------------------------------------------------------------
    def _check_statement_type(self, tree: exp.Expression) -> list[str]:
        allowed = self.config.allowed_statement_types
        if isinstance(tree, exp.Select):
            return []
        if isinstance(tree, exp.With) and isinstance(tree.this, exp.Select):
            return []
        return [f"Statement type '{type(tree).__name__}' is not in allowed_statement_types={sorted(allowed)}"]

    def _check_denied_keywords(self, sql_text: str) -> list[str]:
        # Belt-and-suspenders string check in addition to AST-type checks
        # below — some DDL/DML keywords (GRANT, REVOKE, CALL) don't always
        # round-trip to a distinct sqlglot expression class across dialects.
        upper = sql_text.upper()
        return [
            f"Denied keyword found: {kw}"
            for kw in self.config.denied_keywords
            if kw in upper
        ]

    def _check_select_star(self, tree: exp.Expression) -> list[str]:
        if not self.config.deny_select_star:
            return []
        for select in tree.find_all(exp.Select):
            for projection in select.expressions:
                if isinstance(projection, exp.Star):
                    return ["SELECT * is not allowed — enumerate columns explicitly"]
        return []

    def _check_functions(self, tree: exp.Expression) -> list[str]:
        reasons: list[str] = []
        allowed = self.config.allowed_aggregate_functions | self.config.allowed_window_functions
        for func in tree.find_all(exp.Func):
            name = (func.sql_name() or type(func).__name__).upper()
            is_window = isinstance(func.parent, exp.Window) or func.find_ancestor(exp.Window) is not None
            # Scalar functions used outside aggregation/window context (e.g. simple
            # arithmetic, CAST, DATE_TRUNC) are fine; only flag unknown aggregate-
            # or window-shaped calls that aren't on the allow list.
            if isinstance(func, (exp.AggFunc,)) and name not in allowed:
                reasons.append(f"Aggregate function '{name}' is not in allowed_aggregate_functions")
            if is_window and name not in self.config.allowed_window_functions:
                reasons.append(f"Window function '{name}' is not in allowed_window_functions")
        return reasons

    def _check_external_urls(self, tree: exp.Expression) -> list[str]:
        if not self.config.deny_external_urls:
            return []
        reasons = []
        for lit in tree.find_all(exp.Literal):
            if lit.is_string and ("://" in str(lit.this)):
                reasons.append(f"Literal contains what looks like an external URL: {lit.this!r}")
        return reasons

    def _extract_tables(self, tree: exp.Expression) -> set[str]:
        # Exclude CTE aliases (e.g. `WITH base AS (...)`) — they are not
        # physical assets and must never be checked against approved_assets.
        cte_aliases = {cte.alias for cte in tree.find_all(exp.CTE)}
        return {
            t.sql(dialect="databricks")
            for t in tree.find_all(exp.Table)
            if t.name not in cte_aliases
        }

    def _check_tables(self, tables: set[str]) -> list[str]:
        reasons: list[str] = []
        if len(tables) > self.config.max_tables:
            reasons.append(f"Query references {len(tables)} tables, exceeding max_tables={self.config.max_tables}")
        if self.approved_assets:
            unapproved = {t for t in tables if t not in self.approved_assets}
            if unapproved:
                reasons.append(f"Unapproved table(s) referenced: {sorted(unapproved)}")
        return reasons

    def _check_joins(self, tree: exp.Expression, join_count: int) -> list[str]:
        reasons: list[str] = []
        if join_count > self.config.max_joins:
            reasons.append(f"Query has {join_count} joins, exceeding max_joins={self.config.max_joins}")
        if self.config.deny_cartesian_joins:
            for join in tree.find_all(exp.Join):
                # sqlglot normalizes BOTH an implicit comma-join (`FROM a, b`)
                # AND an explicit `CROSS JOIN` to a Join node with kind="CROSS".
                # A bare `JOIN b` with no ON/USING parses as `on=Boolean(True)`
                # (an "ON TRUE" tautology) rather than `on=None`. All three
                # shapes are cartesian products and are denied outright — this
                # framework has no legitimate use case that needs one.
                on_clause = join.args.get("on")
                has_using = bool(join.args.get("using"))
                is_tautology = isinstance(on_clause, exp.Boolean) and on_clause.this is True
                is_missing_condition = on_clause is None and not has_using
                is_cross_kind = (join.kind or "").upper() == "CROSS"
                if is_cross_kind or is_tautology or is_missing_condition:
                    reasons.append("Cartesian join detected (comma-join, CROSS JOIN, or JOIN with no ON/USING)")
        return reasons

    def _check_limit(self, tree: exp.Expression) -> list[str]:
        if not self.config.require_limit:
            return []
        select = tree if isinstance(tree, exp.Select) else tree.find(exp.Select)
        if select is None or select.args.get("limit") is None:
            return ["Query has no LIMIT clause — a bounded row limit is required"]
        limit_expr = select.args["limit"]
        try:
            limit_value = int(limit_expr.expression.this)
        except (AttributeError, ValueError, TypeError):
            return ["LIMIT clause value could not be statically verified"]
        if limit_value > self.config.max_rows:
            return [f"LIMIT {limit_value} exceeds max_rows={self.config.max_rows}"]
        return []
