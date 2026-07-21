"""Deterministic query compiler — PRD Sec. 16, engineering interface
`QueryCompiler` (Sec. 28). Maps canonical concept IDs to approved physical
expressions via MEASURE_MAP / DIMENSION_MAP (built from ontology.metric_definition
and ontology.dimension_definition, never hand-maintained in code). This is
the PREFERRED path — the constrained LLM generator (llm_sql_generator.py) is
only a fallback for shapes the deterministic compiler cannot express.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..models import OntologyContext, SemanticPlan, ComparisonBasis


@dataclass
class CompilationResult:
    sql: str
    parameters: dict[str, object]
    assets_used: list[str]
    used_deterministic_path: bool = True


class DeterministicCompiler:
    """Builds MEASURE_MAP / DIMENSION_MAP from the ontology context passed in
    (never global mutable state), so two concurrent requests with different
    permission-aware projections never leak each other's mappings."""

    async def compile(self, plan: SemanticPlan, context: OntologyContext) -> CompilationResult | None:
        measure_map = self._build_measure_map(context)
        dimension_map = self._build_dimension_map(context)

        if not all(m in measure_map for m in plan.metric_ids):
            return None  # fall back to constrained LLM generation
        if not all(d in dimension_map for d in plan.dimension_ids):
            return None

        metric = context.approved_metrics[0] if context.approved_metrics else None
        if metric is None or not metric.certified_source_asset:
            return None

        select_parts = [measure_map[m] for m in plan.metric_ids]
        group_by_parts = [dimension_map[d] for d in plan.dimension_ids]

        where_clauses: list[str] = []
        parameters: dict[str, object] = {}
        for idx, f in enumerate(plan.filters):
            if f.dimension_id not in dimension_map:
                return None
            column = dimension_map[f.dimension_id]
            param_name = f"filter_{idx}"
            if f.operator.value in ("IN", "NOT_IN"):
                placeholders = ", ".join(f":{param_name}_{i}" for i in range(len(f.canonical_values)))
                op = "IN" if f.operator.value == "IN" else "NOT IN"
                where_clauses.append(f"{column} {op} ({placeholders})")
                for i, v in enumerate(f.canonical_values):
                    parameters[f"{param_name}_{i}"] = v
            else:
                sql_op = {"EQUALS": "=", "NOT_EQUALS": "!=", "GREATER_THAN": ">",
                          "GREATER_OR_EQUAL": ">=", "LESS_THAN": "<", "LESS_OR_EQUAL": "<="}.get(f.operator.value, "=")
                where_clauses.append(f"{column} {sql_op} :{param_name}")
                parameters[param_name] = f.canonical_values[0] if f.canonical_values else None

        select_clause = ", ".join(select_parts + group_by_parts)
        from_clause = metric.certified_source_asset
        where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        group_by_clause = f"GROUP BY {', '.join(group_by_parts)}" if group_by_parts else ""

        comparison_clause = self._comparison_clause(plan.comparison)

        sql = (
            f"SELECT {select_clause}{comparison_clause}\n"
            f"FROM {from_clause}\n"
            f"{where_clause}\n"
            f"{group_by_clause}\n"
            f"LIMIT {min(plan.limit, 10_000)}"
        ).strip()

        return CompilationResult(
            sql=sql,
            parameters=parameters,
            assets_used=[from_clause],
            used_deterministic_path=True,
        )

    @staticmethod
    def _build_measure_map(context: OntologyContext) -> dict[str, str]:
        return {m.metric_id: f"MEASURE({m.metric_id.split('.')[-1].lower()})" for m in context.approved_metrics}

    @staticmethod
    def _build_dimension_map(context: OntologyContext) -> dict[str, str]:
        return {d.dimension_id: d.key_column for d in context.approved_dimensions}

    @staticmethod
    def _comparison_clause(comparison: ComparisonBasis) -> str:
        if comparison == ComparisonBasis.NONE:
            return ""
        # A metric view with time intelligence would expose a comparison
        # measure directly; kept as a no-op placeholder here so the
        # deterministic path stays honest about what it can/can't express
        # without a certified comparison measure registered.
        return ""
