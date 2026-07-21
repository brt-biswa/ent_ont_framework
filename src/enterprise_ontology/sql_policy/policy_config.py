"""SQL policy configuration — PRD Sec. 14, 16 allow/deny lists and limits.
Kept as data, not scattered constants, so the policy version recorded on
every audit event (PRD Sec. 25) actually means something reviewable.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SQLPolicyConfig:
    version: str = "1.0.0"

    allowed_statement_types: frozenset[str] = field(
        default_factory=lambda: frozenset({"SELECT", "WITH"})
    )
    denied_keywords: frozenset[str] = field(
        default_factory=lambda: frozenset({
            "INSERT", "UPDATE", "DELETE", "MERGE",
            "CREATE", "ALTER", "DROP", "TRUNCATE",
            "GRANT", "REVOKE", "CALL", "EXECUTE IMMEDIATE",
        })
    )
    allowed_aggregate_functions: frozenset[str] = field(
        default_factory=lambda: frozenset({
            "SUM", "AVG", "COUNT", "COUNT_DISTINCT", "MIN", "MAX",
            "MEASURE", "PERCENTILE", "STDDEV", "VARIANCE",
        })
    )
    allowed_window_functions: frozenset[str] = field(
        default_factory=lambda: frozenset({
            "ROW_NUMBER", "RANK", "DENSE_RANK", "LAG", "LEAD", "SUM", "AVG",
        })
    )
    max_tables: int = 6
    max_joins: int = 5
    max_rows: int = 10_000
    max_date_range_days: int = 1100
    query_timeout_seconds: int = 30
    deny_select_star: bool = True
    deny_cartesian_joins: bool = True
    deny_external_urls: bool = True
    require_limit: bool = True


DEFAULT_POLICY = SQLPolicyConfig()
